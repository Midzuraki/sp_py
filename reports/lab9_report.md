# Отчёт по лабораторной работе №9

**«CRUD-операции с базой данных через Python» (SQLite, вариант 3: товары и поставщики)**

## Раздел 1. Цель работы

Целью работы было продолжить проект ЛР8 и написать модуль `crud.py`, выполняющий четыре операции CRUD — добавление, чтение, обновление и удаление — а также поиск по ключевому слову. Все значения передаются через параметризованные запросы, а имена таблиц и колонок, которые параметрами не передать, проверяются по белому списку. На практике нужно было убедиться, чем конкатенация строк в SQL опасна и почему параметры (`?`) защищают от SQL-инъекций. Результат — набор функций, корректно обрабатывающих внешний ключ и ошибки, плюс демонстрация инъекции на копии БД.

## Раздел 2. Порядок выполнения работы

**Шаг 1. Модуль `crud.py`.** Создан в той же папке `src/shop_db/`, где лежат `init_db.py` и `check_db.py`. Путь к БД — первый параметр каждой функции. Каждая функция сама открывает соединение (`_connect` включает `PRAGMA foreign_keys = ON`), выполняет операцию, делает `commit()` при изменении данных и закрывает соединение в `finally`.

**Шаг 2. Create.** `add_supplier(db_path, name, manager, phone)` возвращает `cursor.lastrowid`; `add_product(db_path, name, quantity, price, supplier_id)` возвращает `lastrowid` или, при `sqlite3.IntegrityError` (нет такого поставщика, `CHECK` на цену/количество), печатает сообщение и возвращает `None`. Для наполнения БД написан `seed_data.py` на `executemany` (3 поставщика и 7 товаров; повторный запуск пропускается, если данные уже есть).

**Шаг 3. Read.** `get_all(db_path, table_name)` — `fetchall()`, список кортежей; `get_by_id(db_path, table_name, record_id)` — `fetchone()` с параметром `?`, `None` для несуществующего `id`. Имя таблицы проверяется по белому списку `ALLOWED_COLUMNS`. По варианту добавлена выборка товаров поставщика `select_products_by_supplier` (JOIN).

**Шаг 4. Update и Delete.** `update_record(db_path, table_name, record_id, **fields)` — динамически собирает `SET`, но имена колонок берёт только из белого списка (иначе `ValueError`), значения — через `?`; возвращает `rowcount > 0`. `delete_record(...)` возвращает `True`/`False` по `rowcount`; при попытке удалить родителя с дочерними записями ловит `IntegrityError` и возвращает `False`.

**Шаг 5. Поиск.** `search_child_by_keyword(db_path, keyword)` ищет по названию товара через `LIKE ?`; символы `%` добавляются к *значению* параметра (`f"%{keyword}%"`), а не к SQL-строке; пустая строка возвращает все товары, несуществующее слово — пустой список.

```python
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
```

**Шаг 6. Проверка на SQL-инъекцию** (`test_injection.py`, всё выполняется на **копии** БД во временной папке, которая затем удаляется).

**Шаг 7. Фиксация результата.** В проекте: `crud.py`, `test_injection.py`, `demo_crud.py`, `seed_data.py`, обновлённый `README.md` с описанием API модуля (список функций, параметры, возвращаемые значения).

**Результаты (реальный вывод `python -m shop_db.demo_crud` и `python -m shop_db.test_injection`):**

```text
$ python -m shop_db.demo_crud
== Create ==
add_supplier -> 4
add_product -> 8
Ошибка: не удалось добавить товар «Призрак» (FOREIGN KEY constraint failed).
add_product с несуществующим поставщиком -> None
Ошибка: не удалось добавить товар «Брак» (CHECK constraint failed: price >= 0).
add_product с отрицательной ценой -> None

== Read ==
get_all(suppliers):
   (1, 'ООО «Молочный край»', 'Иванова А.П.', '+7 900 111-22-33')
   (2, 'ИП Петров', 'Петров С.В.', '+7 900 222-33-44')
   (3, 'АО «ХлебТорг»', 'Сидорова Е.Н.', '+7 900 333-44-55')
   (4, 'ООО «Рыбком»', 'Кузнецов Д.А.', '+7 900 555-66-77')
get_by_id(products, 1) -> (1, 'Молоко 3.2%', 120, 79.9, 1)
get_by_id(products, 9999) -> None
Товары поставщика 1:
   (2, 'Кефир 1%', 80, 69.5, 'ООО «Молочный край»')
   (1, 'Молоко 3.2%', 120, 79.9, 'ООО «Молочный край»')
   (3, 'Сметана 20%', 45, 95.0, 'ООО «Молочный край»')

== Update ==
update_record(products, 1, price=84.9, quantity=100) -> True
  после: (1, 'Молоко 3.2%', 100, 84.9, 1)
update_record(products, 9999, price=1) -> False
Ошибка обновления записи 1: FOREIGN KEY constraint failed
update_record(products, 1, supplier_id=777) -> False
update_record с «опасным» именем поля -> Недопустимые поля для products: ['price = 0, name']

== Search ==
'ок'     -> ['Молоко 3.2%', 'Яблоки Антоновка']
'ХЛЕБ'   -> ['Хлеб ржаной']
''       -> найдено 8 из 8
'zzz'    -> []
'%'      -> [(2, 'Кефир 1%', 80, 69.5, 1), (1, 'Молоко 3.2%', 100, 84.9, 1), (3, 'Сметана 20%', 45, 95.0, 1)] (% экранирован: найдены только названия с символом %)

== Delete ==
Нельзя удалить запись 1 из suppliers: на неё есть ссылки (FOREIGN KEY constraint failed).
delete_record(suppliers, 1) (есть товары) -> False
после удаления товаров: delete_record(suppliers, 1) -> True
delete_record(suppliers, 1) ещё раз -> False

$ python -m shop_db.test_injection
Работаем с копией: /tmp/tmp5cgtfifk/copy.db
Таблицы до начала: ['products', 'suppliers']

1) Конкатенация + execute():
   Ошибка ProgrammingError: You can only execute one statement at a time.
   Таблицы: ['products', 'suppliers']
2) Конкатенация + executescript() (так пишут «наивно»):
   Таблицы: ['suppliers']   <- таблица products уничтожена!
3) Конкатенация в SELECT, ввод «' OR '1'='1»:
   найдено строк: 7 (хотя товара с таким названием нет)
4) Параметризованные запросы из crud.py:
   add_supplier -> id=4; сохранено как обычный текст: "x'); DROP TABLE products; --"
   таблицы: ['products', 'suppliers']   <- всё цело
   search_child_by_keyword("' OR '1'='1") -> []

Копия удалена, рабочая БД не тронута.
```

Что подтверждает вывод:

* **Create:** `add_supplier` вернул `4`, `add_product` — `8`; вставка с несуществующим поставщиком и с отрицательной ценой возвращает `None`, программа не падает.
* **Read:** для `id = 9999` возвращается `None`; выборка товаров поставщика 1 выдаёт три товара вместе с названием поставщика.
* **Update:** найденная запись обновляется (`True`), несуществующая — `False`; смена `supplier_id` на несуществующий вернула `False`; «опасное» имя поля отвергнуто `ValueError`.
* **Search:** фрагмент слова, регистр (включая кириллицу), пустая строка (8 из 8), несуществующее слово (`[]`), `%` как обычный символ.
* **Delete:** удалить поставщика с товарами нельзя (`False`), после удаления товаров — можно (`True`), повторное удаление — `False`.
* **Инъекция:** `execute()` с конкатенацией отклоняет несколько операторов (`ProgrammingError`), но `executescript()` с той же строкой **уничтожил таблицу `products`**; ввод `' OR '1'='1` в `SELECT` с конкатенацией вернул все 7 строк; параметризованные функции записали вредоносную строку как обычный текст и оставили обе таблицы целыми.

## Раздел 3. Таблица промптов и ответов ИИ

| № | Промпт (запрос к ИИ) | Ответ ИИ (кратко) | Анализ результата |
| --- | --- | --- | --- |
| 1 | «Чем `cursor.execute()` отличается от `executemany()` и что возвращает `cursor.lastrowid`?» | `execute` — один запрос; `executemany` — один шаблон для последовательности наборов параметров (удобно для наполнения). `lastrowid` — id последней вставленной строки, обновляется после `INSERT` через `execute()`. | Применил: `executemany` в `seed_data.py` (сначала поставщики, затем товары), `lastrowid` — в `add_supplier`/`add_product`. Принял к сведению, что после `executemany` `lastrowid` не обновляется, поэтому для получения id использую `execute`. |
| 2 | «Почему значения нельзя подставлять в SQL через f-строку? Что произойдёт при вводе `'); DROP TABLE teachers; --` и почему параметризованный запрос это не допускает?» | Строка становится частью SQL-кода, и ввод может завершить оператор и добавить свой. В параметризованном запросе значение передаётся отдельно от текста запроса и всегда трактуется как данные. | Проверил на копии БД: `execute()` с конкатенацией дал `ProgrammingError`, а `executescript()` удалил таблицу; параметризованный `add_supplier` сохранил вредоносную строку как текст. |
| 3 | «Как динамически собрать `SET` в `UPDATE` из `**fields` и не получить SQL-инъекцию через имя поля?» | Имена колонок через `?` передать нельзя — их проверяют по белому списку допустимых колонок таблицы, значения — через `?`. | Реализовал `ALLOWED_COLUMNS`. Проверил на «опасном» имени `price = 0, name`: без белого списка получается `UPDATE products SET price = 0, name = ? ...` и обнуляется цена, с белым списком — `ValueError`. |
| 4 | «Как реализовать поиск через `LIKE` с параметром? Куда ставить `%` и как искать без учёта регистра по кириллице?» | `%` включают в значение параметра: `pattern = f"%{keyword}%"`. Регистр: `LOWER(name) LIKE ?`. | Первая версия с `LIKE ?` не находила «ХЛЕБ» → «Хлеб ржаной» (`[]`): `LIKE` и `LOWER` в SQLite нечувствительны к регистру только для латиницы. Решил регистрацией функции `PYLOWER` через `conn.create_function` (улучшение №1). |
| 5 | «Что показывает `cursor.rowcount` после `UPDATE`/`DELETE`, почему он не подходит для `SELECT` и как по нему понять, что запись не найдена?» | Число изменённых строк; для `SELECT` значение −1/не определено; `rowcount == 0` — ничего не найдено/не изменено. | Использовал в `update_record` и `delete_record` (`return cursor.rowcount > 0`), проверил на `id = 9999` — `False`. |
| 6 | «Что произойдёт при удалении родительской записи, на которую ссылаются дочерние? Как правильно обработать в `delete_record`? В каком порядке удалять?» | Из-за внешнего ключа будет `sqlite3.IntegrityError` (с включённым PRAGMA); нужно `try/except` с `rollback`/возвратом `False`; сначала удалять дочерние, затем родителя (или `ON DELETE CASCADE`). | Реализовал `try/except sqlite3.IntegrityError` → `False`; в демонстрации сначала удалил товары поставщика, затем поставщика — получилось. |
| 7 | «Вот мой `search_child_by_keyword` (вставляю код). Найди 2 возможные проблемы.» | (1) Если пользователь введёт `%` или `_`, они сработают как шаблоны. (2) Без `ORDER BY` порядок результата не гарантирован. | Подтвердил: ввод `%` возвращал все строки; добавил экранирование и `ESCAPE '\'` (улучшение №2). `ORDER BY name` в запросе уже есть. |

## Раздел 4. Таблица улучшений кода

В №1 «старый код» — реальная предыдущая версия `crud.py`, в №2 и №3 — черновые варианты, проблемы которых воспроизведены запуском.

| № | Старый код | Новый код (фрагмент) | Пояснение (зачем изменено) |
| --- | --- | --- | --- |
| 1 | `"WHERE name LIKE ? ESCAPE '\\' ORDER BY name"`<br>`pattern = f"%{escaped}%"` | `conn.create_function("PYLOWER", 1, lambda v: v.casefold() if isinstance(v, str) else v, deterministic=True)`<br>`"WHERE PYLOWER(name) LIKE ? ESCAPE '\\' ORDER BY name"`<br>`pattern = f"%{escaped.casefold()}%"` | Встроенный `LIKE` в SQLite не учитывает регистр только для латиницы: поиск «ХЛЕБ» возвращал `[]`. Теперь «ХЛЕБ» находит «Хлеб ржаной» (проверено запуском). |
| 2 | `pattern = f"%{keyword}%"` | `escaped = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")`<br>`pattern = f"%{escaped.casefold()}%"` | Пользовательские `%` и `_` в шаблоне работали как подстановочные символы: ввод `%` возвращал все товары (проверено). Теперь они ищутся как обычные символы: `%` находит только «Кефир 1%», «Молоко 3.2%», «Сметана 20%». |
| 3 | `set_clause = ", ".join(f"{k} = ?" for k in fields)` (без проверки имён) | `unknown = set(fields) - set(ALLOWED_COLUMNS[table_name])`<br>`if unknown:`<br>`    raise ValueError(f"Недопустимые поля для {table_name}: {sorted(unknown)}")` | Имя колонки подставляется в SQL-строку, а не через `?`; вызов с ключом `"price = 0, name"` превращался в `SET price = 0, name = ?` и менял чужие поля (проверено). Белый список закрывает инъекцию через имя поля. |

Подтверждение для №1–№3 (реальный вывод черновых вариантов):

```text
### ЛР9: LIKE и кириллица / % без экранирования / динамический SET без белого списка
LIKE '%ХЛЕБ%' -> []
LIKE '%%%' (ввод '%') -> 3 из 3 (вернулись все)
SQL без белого списка: UPDATE products SET price = 0, name = ? WHERE id = ?
цены после: [('взлом', 0.0), ('Молоко 3.2%', 80.0), ('Батон', 48.0)]
```

## Раздел 5. Ответы на контрольные вопросы

**1. В чём разница между `cursor.execute()` и `cursor.executemany()`? Что возвращает `cursor.lastrowid`?**
`execute(sql, params)` выполняет один запрос с одним набором параметров — нужен для единичных операций (добавить поставщика, найти товар). `executemany(sql, seq_of_params)` выполняет один и тот же запрос для каждого набора из последовательности — нужен для массового наполнения (`seed_data.py`). `cursor.lastrowid` — идентификатор (`rowid`) последней вставленной строки; обновляется после `INSERT` через `execute()` (после `executemany`, `executescript` или неудачной вставки значение не меняется). Его используют, чтобы сразу добавить дочерние записи с `supplier_id`.

**2. Почему значения передаются через `?`, а не через f-строку? Что будет с вводом `'); DROP TABLE teachers; --` и почему параметры этого не допускают?**
При f-строке или конкатенации ввод попадает в текст SQL и может закрыть строку и оператор, а затем выполнить чужую команду (`DROP TABLE`) и закомментировать остаток (`--`). В моём опыте на копии БД `executescript()` с такой строкой удалил таблицу. В параметризованном запросе текст запроса и данные передаются отдельно: драйвер подставляет значение как данные, оно никогда не разбирается как SQL, поэтому вредоносная строка просто сохраняется как текст (проверено: `x'); DROP TABLE products; --` записана в поле `name`, таблицы целы).

**3. Чем отличаются `fetchone()`, `fetchall()`, `fetchmany(n)`? Что вернут при пустом результате? Зачем `row_factory = sqlite3.Row`?**
`fetchone()` — одна следующая строка (кортеж) или `None`, если строк нет; `fetchall()` — список всех оставшихся строк (при пустом результате `[]`); `fetchmany(n)` — список не более `n` строк (пустой список, если строки закончились). `conn.row_factory = sqlite3.Row` заставляет возвращать строки в виде объектов, к полям которых можно обращаться по имени (`row["name"]`) и по индексу, что делает код устойчивее к изменению порядка колонок.

**4. Что показывает `cursor.rowcount` после `UPDATE` и `DELETE`? Почему нельзя судить по нему о числе строк `SELECT`? Как определить, что запись не найдена?**
После `UPDATE`/`DELETE` (и `INSERT`) `rowcount` — число затронутых строк. Для `SELECT` значение не определено (в `sqlite3` это `-1`): число строк результата становится известным только при выборке (`fetchall`), поэтому для запросов на чтение `rowcount` не используют. Если `rowcount == 0` после `UPDATE`/`DELETE` по `id`, запись с таким `id` не найдена — именно так `update_record` и `delete_record` возвращают `False`.

**5. Почему при удалении родительской записи с дочерними возникает `IntegrityError`? Как обработать в `delete_record`? В каком порядке удалять связанные записи?**
Внешний ключ гарантирует, что каждая дочерняя запись ссылается на существующего родителя; удаление родителя оставило бы «осиротевшие» записи, поэтому при включённом `PRAGMA foreign_keys` (действие `NO ACTION` по умолчанию) SQLite отклоняет операцию с `IntegrityError: FOREIGN KEY constraint failed`. В `delete_record` ошибка перехватывается (`except sqlite3.IntegrityError`), выполняется `rollback()`, выводится сообщение и возвращается `False`. Удалять нужно в обратном порядке создания: сначала дочерние записи (`products`), потом родительскую (`suppliers`) — или заранее объявить `ON DELETE CASCADE`, если каскадное удаление допустимо по смыслу.

## Раздел 6. Выводы

В ходе работы я реализовал полный набор CRUD-операций и поиск на SQLite через параметризованные запросы и убедился на практике, почему так нужно: конкатенация строк с `executescript()` уничтожила таблицу, а параметры сохранили вредоносный ввод как обычный текст. Я научился защищать динамические части запроса — имена колонок проверяются по белому списку, а `%` и `_` в `LIKE` экранируются. Неожиданной находкой стало поведение `LIKE` в SQLite с кириллицей: регистр не учитывается только для латиницы, поэтому пришлось зарегистрировать собственную функцию. Я освоил `cursor.lastrowid` и `cursor.rowcount` и использую их, чтобы возвращать `id` и логический результат операций. Особое внимание уделил обработке `IntegrityError` для внешнего ключа: функции не падают, а возвращают `None`/`False`. Самым полезным навыком считаю привычку никогда не склеивать SQL из пользовательских данных и проверять опасные сценарии на копии базы. Я понимаю код `crud.py` и могу объяснить каждую функцию.
