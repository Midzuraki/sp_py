"""Проверка структуры БД: внешние ключи, таблицы, поля, внешние ключи дочерней таблицы.

Запуск:  python -m shop_db.check_db [путь_к_файлу_БД]
"""
import sqlite3
import sys
from pathlib import Path
from typing import Union

from shop_db.config import DEFAULT_DB_PATH


def check_db(db_path: Union[str, Path] = DEFAULT_DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA foreign_keys;")
        enabled = bool(cursor.fetchone()[0])
        print(f"Внешние ключи включены: {enabled}")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' "
                       "AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Таблицы: {tables}")

        for table in tables:
            print(f"\nТаблица {table}: (cid, name, type, notnull, dflt_value, pk)")
            cursor.execute(f"PRAGMA table_info({table});")  # имя таблицы взято из sqlite_master
            for column in cursor.fetchall():
                print(f"  {column}")

        print("\nВнешние ключи таблицы products:")
        cursor.execute("PRAGMA foreign_key_list(products);")
        # (id, seq, table, from, to, on_update, on_delete, match)
        for fk in cursor.fetchall():
            print(f"  {fk}")
            print(f"  {fk[3]} -> {fk[2]}.{fk[4]}")
    finally:
        conn.close()


if __name__ == "__main__":
    check_db(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH)
