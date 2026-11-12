"""Проверка ссылочной целостности: вставка товара с несуществующим supplier_id.

Запуск:  python -m shop_db.check_integrity [путь_к_файлу_БД]
"""
import sqlite3
import sys
from pathlib import Path
from typing import Union

from shop_db.config import DEFAULT_DB_PATH

INSERT = "INSERT INTO products (name, quantity, price, supplier_id) VALUES (?, ?, ?, ?)"
FAKE_ROW = ("Тестовый товар", 1, 10.0, 99999)  # поставщика 99999 нет


def try_insert(db_path: Union[str, Path], foreign_keys_on: bool) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        if foreign_keys_on:
            cursor.execute("PRAGMA foreign_keys = ON;")
        try:
            cursor.execute(INSERT, FAKE_ROW)
            # commit() намеренно не вызываем: проверка не должна оставлять следов в БД
            print("  Запись вставлена - внешний ключ НЕ работает.")
        except sqlite3.IntegrityError as error:
            print(f"  Ошибка целостности ({error}) - внешний ключ работает корректно.")
        finally:
            conn.rollback()  # откатываем: тестовая запись не остаётся в БД
    finally:
        conn.close()


def check_integrity(db_path: Union[str, Path] = DEFAULT_DB_PATH) -> None:
    print("1) С PRAGMA foreign_keys = ON:")
    try_insert(db_path, foreign_keys_on=True)
    print("2) БЕЗ PRAGMA foreign_keys = ON (типичная ошибка):")
    try_insert(db_path, foreign_keys_on=False)


if __name__ == "__main__":
    check_integrity(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH)
