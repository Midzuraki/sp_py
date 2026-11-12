"""Демонстрация SQL-инъекции на КОПИИ базы: конкатенация строк vs параметры (?).

Запуск:  python -m shop_db.test_injection [путь_к_файлу_БД]
Рабочая БД не затрагивается: копия создаётся во временной папке и удаляется.
"""
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

from shop_db import crud
from shop_db.config import DEFAULT_DB_PATH
from shop_db.seed_data import seed

EVIL_NAME = "x'); DROP TABLE products; --"


def tables(db: Path) -> list:
    conn = sqlite3.connect(db)
    try:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' "
                            "AND name NOT LIKE 'sqlite_%'").fetchall()
        return sorted(r[0] for r in rows)
    finally:
        conn.close()


def main() -> None:
    source = Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH)
    if not source.exists():
        seed(source)
    workdir = Path(tempfile.mkdtemp())
    copy = workdir / "copy.db"
    shutil.copy(source, copy)
    print(f"Работаем с копией: {copy}\nТаблицы до начала: {tables(copy)}\n")

    # --- 1. Наивная конкатенация + execute: sqlite3 разрешает один оператор за вызов ---
    print("1) Конкатенация + execute():")
    conn = sqlite3.connect(copy)
    try:
        conn.execute("INSERT INTO suppliers (name) VALUES ('" + EVIL_NAME + "')")
        print("   запрос выполнен")
    except sqlite3.Error as error:
        print(f"   Ошибка {type(error).__name__}: {error}")
    finally:
        conn.close()
    print(f"   Таблицы: {tables(copy)}")

    # --- 2. Наивная конкатенация + executescript: выполняются ВСЕ операторы ---
    print("2) Конкатенация + executescript() (так пишут «наивно»):")
    conn = sqlite3.connect(copy)
    try:
        conn.executescript("INSERT INTO suppliers (name) VALUES ('" + EVIL_NAME + "')")
    except sqlite3.Error as error:
        print(f"   Ошибка {type(error).__name__}: {error}")
    finally:
        conn.close()
    print(f"   Таблицы: {tables(copy)}   <- таблица products уничтожена!")

    # Восстанавливаем копию для следующих опытов
    shutil.copy(source, copy)

    # --- 3. Инъекция в SELECT: условие превращается в «всегда истина» ---
    print("3) Конкатенация в SELECT, ввод «' OR '1'='1»:")
    evil_search = "' OR '1'='1"
    conn = sqlite3.connect(copy)
    rows = conn.execute("SELECT name FROM products WHERE name = '" + evil_search + "'").fetchall()
    conn.close()
    print(f"   найдено строк: {len(rows)} (хотя товара с таким названием нет)")

    # --- 4. Те же вводы через параметризованные функции crud.py ---
    print("4) Параметризованные запросы из crud.py:")
    new_id = crud.add_supplier(copy, EVIL_NAME, "Хакер", "000")
    print(f"   add_supplier -> id={new_id}; сохранено как обычный текст: "
          f"{crud.get_by_id(copy, 'suppliers', new_id)[1]!r}")
    print(f"   таблицы: {tables(copy)}   <- всё цело")
    print(f"   search_child_by_keyword({evil_search!r}) -> {crud.search_child_by_keyword(copy, evil_search)}")

    shutil.rmtree(workdir)
    print("\nКопия удалена, рабочая БД не тронута.")


if __name__ == "__main__":
    main()
