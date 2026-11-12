"""CRUD-операции и поиск. Путь к БД - параметр каждой функции, запросы - параметризованные."""
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

PathLike = Union[str, Path]

# Белые списки: имена таблиц и колонок НЕЛЬЗЯ передавать через ?, поэтому проверяем сами
ALLOWED_COLUMNS: Dict[str, Tuple[str, ...]] = {
    "suppliers": ("name", "manager", "phone"),
    "products": ("name", "quantity", "price", "supplier_id"),
}


def _connect(db_path: PathLike) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")  # при КАЖДОМ подключении
    # Встроенные LOWER/LIKE в SQLite понимают регистр только у латиницы (ASCII),
    # поэтому для поиска без учёта регистра по кириллице регистрируем свою функцию.
    conn.create_function("PYLOWER", 1, lambda v: v.casefold() if isinstance(v, str) else v,
                         deterministic=True)
    return conn


def _check_table(table_name: str) -> None:
    if table_name not in ALLOWED_COLUMNS:
        raise ValueError(f"Неизвестная таблица: {table_name!r}")


# ---------- Create ----------
def add_supplier(
    db_path: PathLike, name: str, manager: Optional[str] = None, phone: Optional[str] = None
) -> int:
    conn = _connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO suppliers (name, manager, phone) VALUES (?, ?, ?)",
            (name, manager, phone),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def add_product(
    db_path: PathLike, name: str, quantity: int, price: float, supplier_id: int
) -> Optional[int]:
    """Возвращает id нового товара или None, если нарушено ограничение (нет поставщика и т.п.)."""
    conn = _connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (name, quantity, price, supplier_id) VALUES (?, ?, ?, ?)",
            (name, quantity, price, supplier_id),
        )
        conn.commit()
        return int(cursor.lastrowid)
    except sqlite3.IntegrityError as error:
        conn.rollback()
        print(f"Ошибка: не удалось добавить товар «{name}» ({error}).")
        return None
    finally:
        conn.close()


# ---------- Read ----------
def get_all(db_path: PathLike, table_name: str) -> List[Tuple[Any, ...]]:
    _check_table(table_name)
    conn = _connect(db_path)
    try:
        cursor = conn.cursor()
        # имя таблицы проверено по белому списку, значения здесь не передаются
        cursor.execute(f"SELECT * FROM {table_name}")
        return cursor.fetchall()
    finally:
        conn.close()


def get_by_id(db_path: PathLike, table_name: str, record_id: int) -> Optional[Tuple[Any, ...]]:
    _check_table(table_name)
    conn = _connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,))
        return cursor.fetchone()  # None, если записи нет
    finally:
        conn.close()


def select_products_by_supplier(db_path: PathLike, supplier_id: int) -> List[Tuple[Any, ...]]:
    """Выборка по варианту: все товары одного поставщика (JOIN двух таблиц)."""
    conn = _connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT p.id, p.name, p.quantity, p.price, s.name "
            "FROM products AS p JOIN suppliers AS s ON s.id = p.supplier_id "
            "WHERE s.id = ? ORDER BY p.name",
            (supplier_id,),
        )
        return cursor.fetchall()
    finally:
        conn.close()


# ---------- Update ----------
def update_record(db_path: PathLike, table_name: str, record_id: int, **fields: Any) -> bool:
    """True - запись найдена и обновлена, False - записи нет (или нарушено ограничение)."""
    _check_table(table_name)
    if not fields:
        raise ValueError("Не переданы поля для обновления")
    unknown = set(fields) - set(ALLOWED_COLUMNS[table_name])
    if unknown:  # имя колонки попадает в SQL-строку - только из белого списка!
        raise ValueError(f"Недопустимые поля для {table_name}: {sorted(unknown)}")

    set_clause = ", ".join(f"{column} = ?" for column in fields)
    values = list(fields.values()) + [record_id]
    conn = _connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE id = ?", values)
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.IntegrityError as error:
        conn.rollback()
        print(f"Ошибка обновления записи {record_id}: {error}")
        return False
    finally:
        conn.close()


# ---------- Delete ----------
def delete_record(db_path: PathLike, table_name: str, record_id: int) -> bool:
    """True - удалено, False - записи нет или на неё ссылаются дочерние записи."""
    _check_table(table_name)
    conn = _connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.IntegrityError as error:
        conn.rollback()
        print(f"Нельзя удалить запись {record_id} из {table_name}: на неё есть ссылки ({error}).")
        return False
    finally:
        conn.close()


# ---------- Поиск ----------
def search_child_by_keyword(db_path: PathLike, keyword: str) -> List[Tuple[Any, ...]]:
    """Поиск товаров по фрагменту названия. Wildcard % - в ЗНАЧЕНИИ параметра, не в SQL."""
    # Символы % и _ из ввода пользователя экранируем, чтобы они искались как обычные
    escaped = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped.casefold()}%"  # шаблон и поле сравниваем в нижнем регистре
    conn = _connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, quantity, price, supplier_id FROM products "
            "WHERE PYLOWER(name) LIKE ? ESCAPE '\\' ORDER BY name",
            (pattern,),
        )
        return cursor.fetchall()
    finally:
        conn.close()
