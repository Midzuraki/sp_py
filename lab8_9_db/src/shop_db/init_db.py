"""Создание БД: сначала родительская таблица suppliers, затем дочерняя products.

Запуск:  python -m shop_db.init_db [путь_к_файлу_БД]
"""
import sqlite3
import sys
from pathlib import Path
from typing import Union

from shop_db.config import DEFAULT_DB_PATH

CREATE_SUPPLIERS = """
CREATE TABLE IF NOT EXISTS suppliers (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL,
    manager TEXT,
    phone   TEXT
);
"""

CREATE_PRODUCTS = """
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    quantity    INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    price       REAL    NOT NULL CHECK (price >= 0),
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id)
);
"""


def init_db(db_path: Union[str, Path] = DEFAULT_DB_PATH) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)  # папку data/ создаём сами
    conn = sqlite3.connect(path)
    try:
        cursor = conn.cursor()
        # Настройка СОЕДИНЕНИЯ, а не файла БД: выполняется при каждом подключении
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute(CREATE_SUPPLIERS)  # родитель - первым, чтобы ссылка разрешилась
        cursor.execute(CREATE_PRODUCTS)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH
    init_db(target)
    print(f"База данных создана: {target}")
