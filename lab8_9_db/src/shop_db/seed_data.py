"""Наполнение БД тестовыми данными через executemany.

Запуск:  python -m shop_db.seed_data [путь_к_файлу_БД]
"""
import sqlite3
import sys
from pathlib import Path
from typing import Union

from shop_db.config import DEFAULT_DB_PATH
from shop_db.init_db import init_db

SUPPLIERS = [
    ("ООО «Молочный край»", "Иванова А.П.", "+7 900 111-22-33"),
    ("ИП Петров", "Петров С.В.", "+7 900 222-33-44"),
    ("АО «ХлебТорг»", "Сидорова Е.Н.", "+7 900 333-44-55"),
]
# (name, quantity, price, supplier_id)
PRODUCTS = [
    ("Молоко 3.2%", 120, 79.90, 1),
    ("Кефир 1%", 80, 69.50, 1),
    ("Сметана 20%", 45, 95.00, 1),
    ("Яблоки Антоновка", 300, 120.00, 2),
    ("Груши Конференция", 150, 180.00, 2),
    ("Хлеб ржаной", 60, 55.00, 3),
    ("Батон нарезной", 90, 48.00, 3),
]


def seed(db_path: Union[str, Path] = DEFAULT_DB_PATH) -> None:
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("SELECT COUNT(*) FROM suppliers")
        if cursor.fetchone()[0]:
            print("В БД уже есть данные - наполнение пропущено.")
            return
        # Сначала родители, потом потомки (иначе нарушится внешний ключ)
        cursor.executemany("INSERT INTO suppliers (name, manager, phone) VALUES (?, ?, ?)", SUPPLIERS)
        cursor.executemany(
            "INSERT INTO products (name, quantity, price, supplier_id) VALUES (?, ?, ?, ?)",
            PRODUCTS,
        )
        conn.commit()
        print(f"Добавлено: поставщиков - {len(SUPPLIERS)}, товаров - {len(PRODUCTS)}.")
    finally:
        conn.close()


if __name__ == "__main__":
    seed(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH)
