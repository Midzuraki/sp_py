# Отчёт по лабораторной работе №8

**«База данных из двух связанных таблиц» (SQLite, вариант 3: товары и поставщики)**

## Раздел 1. Цель работы

Целью работы было спроектировать и создать базу данных SQLite из двух таблиц, связанных внешним ключом «один ко многим», работая только через Python-скрипты. Предметная область — вариант 3: товары (наименование, количество, цена, поставщик) и поставщики (название, менеджер, телефон). Я спроектировал структуру проекта и таблиц, написал скрипт создания БД, скрипт проверки структуры через служебные таблицы и `PRAGMA`, а также скрипт, доказывающий, что внешний ключ действительно защищает целостность данных.

## Раздел 2. Порядок выполнения работы

**Шаг 1. Структура проекта.** Спроектировал дерево до написания кода (полностью с пояснением к каждому элементу — в `lab8_9_db/README.md`):

```text
lab8_9_db/
├── .gitignore, pyproject.toml, README.md
├── data/            (.gitkeep, myapp.db)
└── src/shop_db/     (__init__, config, init_db, check_db, check_integrity, [seed_data, crud, ... из ЛР9])
```

Файл `.db` — результат работы скрипта, поэтому он вынесен в `data/` и добавлен в `.gitignore`, а саму папку сохраняет `.gitkeep`.

**Шаг 2. Окружение.** Модуль `sqlite3` входит в стандартную библиотеку. Создан `pyproject.toml` (имя, версия, описание, автор, `requires-python = ">=3.9"`, `dependencies = []`, `[build-system]` на setuptools, `[tool.setuptools.packages.find] where = ["src"]`), `.gitignore` (`.venv/`, `__pycache__/`, `*.db`, `*.sqlite`, `*.sqlite3`, `data/*` и исключение `!data/.gitkeep`). Установка: `pip install -e .`.

**Шаг 3. Определение таблиц и связи.**

```text
Родительская таблица:   suppliers (поставщики)
Дочерняя таблица:       products  (товары)
Поле-связка в дочерней: supplier_id INTEGER REFERENCES suppliers(id)
```

**Шаг 4. Проектирование таблиц** (после шагов 1–4 я сдал README на проверку, как требует задание).

*Родительская таблица `suppliers`:*

| Имя поля | Тип | Ограничения | Назначение |
| --- | --- | --- | --- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный номер поставщика |
| name | TEXT | NOT NULL | Название поставщика |
| manager | TEXT | — | Менеджер |
| phone | TEXT | — | Телефон |

*Дочерняя таблица `products`:*

| Имя поля | Тип | Ограничения | Назначение |
| --- | --- | --- | --- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный номер товара |
| name | TEXT | NOT NULL | Наименование товара |
| quantity | INTEGER | NOT NULL DEFAULT 0, CHECK (quantity >= 0) | Количество на складе |
| price | REAL | NOT NULL, CHECK (price >= 0) | Цена |
| supplier_id | INTEGER | NOT NULL, REFERENCES suppliers(id) | Ссылка на поставщика |

**Шаг 5. `init_db.py`.** Подключается к `data/myapp.db` (путь — параметр функции, значение по умолчанию в `config.py`; папка создаётся `Path.parent.mkdir(parents=True, exist_ok=True)`), выполняет `PRAGMA foreign_keys = ON;`, затем `CREATE TABLE IF NOT EXISTS` для родителя и потом для потомка, делает `commit()` и закрывает соединение.

```python
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
```

**Шаг 6. `check_db.py`.** Выводит состояние внешних ключей, список таблиц из `sqlite_master`, поля каждой таблицы (`PRAGMA table_info`) и внешние ключи дочерней таблицы (`PRAGMA foreign_key_list`).

**Шаг 7. `check_integrity.py`.** Пытается вставить товар с несуществующим `supplier_id = 99999`: с `PRAGMA foreign_keys = ON` ловит `IntegrityError`, затем повторяет опыт без PRAGMA, показывая типичную ошибку. Тестовая запись откатывается (`rollback()`).

**Шаг 8. Результат** (реальный вывод запуска скриптов; файл `data/myapp.db` создан и после проверок остаётся чистым):

```text
$ python -m shop_db.init_db
База данных создана: /mnt/user-data/outputs/sp_py/lab8_9_db/data/myapp.db
$ python -m shop_db.init_db   # повторный запуск (IF NOT EXISTS)
База данных создана: /mnt/user-data/outputs/sp_py/lab8_9_db/data/myapp.db

$ python -m shop_db.check_db
Внешние ключи включены: True
Таблицы: ['suppliers', 'products']

Таблица suppliers: (cid, name, type, notnull, dflt_value, pk)
  (0, 'id', 'INTEGER', 0, None, 1)
  (1, 'name', 'TEXT', 1, None, 0)
  (2, 'manager', 'TEXT', 0, None, 0)
  (3, 'phone', 'TEXT', 0, None, 0)

Таблица products: (cid, name, type, notnull, dflt_value, pk)
  (0, 'id', 'INTEGER', 0, None, 1)
  (1, 'name', 'TEXT', 1, None, 0)
  (2, 'quantity', 'INTEGER', 1, '0', 0)
  (3, 'price', 'REAL', 1, None, 0)
  (4, 'supplier_id', 'INTEGER', 1, None, 0)

Внешние ключи таблицы products:
  (0, 0, 'suppliers', 'supplier_id', 'id', 'NO ACTION', 'NO ACTION', 'NONE')
  supplier_id -> suppliers.id

$ python -m shop_db.check_integrity
1) С PRAGMA foreign_keys = ON:
  Ошибка целостности (FOREIGN KEY constraint failed) - внешний ключ работает корректно.
2) БЕЗ PRAGMA foreign_keys = ON (типичная ошибка):
  Запись вставлена - внешний ключ НЕ работает.

$ python -m shop_db.seed_data
Добавлено: поставщиков - 3, товаров - 7.
$ python -m shop_db.seed_data   # повторно
В БД уже есть данные - наполнение пропущено.
```

Вывод `check_db.py` подтверждает: внешние ключи включены (`True`), обе таблицы на месте, у `id` в обеих таблицах `pk = 1`, а в `PRAGMA foreign_key_list` есть строка `supplier_id -> suppliers.id`. Проверка целостности: с PRAGMA вставка отклонена, без PRAGMA — «проходит молча» (поэтому PRAGMA нужно выполнять в каждом соединении).

Структура проекта по заданию: `init_db.py`, `check_db.py`, `check_integrity.py`, `data/myapp.db`, `README.md`, `.gitignore` (исключает `.db` и кеши, но сохраняет `data/`).

Дополнительно (к ЛР9) реализованы выборка товаров по поставщику и поиск по названию товара — требуемые вариантом (`select_products_by_supplier`, `search_child_by_keyword` в `crud.py`).

## Раздел 3. Таблица промптов и ответов ИИ

| № | Промпт (запрос к ИИ) | Ответ ИИ (кратко) | Анализ результата |
| --- | --- | --- | --- |
| 1 | «Как в SQLite объявить связь «один ко многим» между поставщиками и товарами? Какая таблица родительская, где пишется `REFERENCES` и какие типы лучше выбрать?» | `suppliers` — родитель (сторона «один»), `products` — потомок; в потомке поле `supplier_id INTEGER REFERENCES suppliers(id)`. Первичный ключ — `INTEGER PRIMARY KEY AUTOINCREMENT`. | Применил. Дополнительно сделал `supplier_id NOT NULL`: по условию варианта у каждого товара обязательно есть поставщик. |
| 2 | «Зачем нужна `PRAGMA foreign_keys = ON` в SQLite и почему её нужно выполнять после каждого подключения?» | В SQLite внешние ключи по умолчанию не проверяются (совместимость); настройка действует на соединение и не хранится в файле БД. | Подтвердил запуском `check_integrity.py`: без PRAGMA вставка с `supplier_id=99999` прошла «молча». |
| 3 | «Что возвращают `PRAGMA table_info` и `PRAGMA foreign_key_list`? Объясни каждый элемент кортежа.» | `table_info`: `(cid, name, type, notnull, dflt_value, pk)`; `foreign_key_list`: `(id, seq, table, from, to, on_update, on_delete, match)`. | Сопоставил с реальным выводом `check_db.py` и вывел строку `supplier_id -> suppliers.id` из элементов `from`, `table`, `to`. |
| 4 | «Как правильно оформить `.gitignore` для файла БД в `data/` и сохранить саму папку в Git? Чем `data/` отличается от `data/*`?» | `data/*` игнорирует содержимое; `!data/.gitkeep` оставляет заглушку; `data/` исключает папку целиком, и исключение не сработает. | Проверил настоящим `git` в ЛР7 (папка исчезала с правилом `data/`). Применил тот же шаблон. |
| 5 | «Что произойдёт, если создать дочернюю таблицу раньше родительской? Почему `init_db.py` создаёт родительскую первой?» | В других СУБД `CREATE TABLE` завершится ошибкой; в SQLite ссылку проверяют при вставке. | Проверил: в SQLite создание проходит, но `INSERT` в потомок падает с `no such table: main.suppliers`, пока родитель не создан. Порядок «родитель → потомок» всё равно правильный и переносимый. |
| 6 | «Вот мой `check_integrity.py` (вставляю код). Найди 2 потенциальные проблемы.» | (1) Если PRAGMA забыть, тестовая запись реально сохранится — нужен откат. (2) С `AUTOINCREMENT` даже удалённая запись «съедает» идентификатор. | Проверил: версия с `commit()` и ручным `DELETE` оставляла «дыру» в нумерации (первая реальная запись получала `id = 2`). Заменил на `rollback()` (улучшение №2). |

## Раздел 4. Таблица улучшений кода

«Старый код» в №1 и №3 — черновики (проблема воспроизведена запуском), в №2 — реальная предыдущая версия `check_integrity.py`.

| № | Старый код | Новый код (фрагмент) | Пояснение (зачем изменено) |
| --- | --- | --- | --- |
| 1 | `CREATE TABLE products (...)`<br>`CREATE TABLE suppliers (...)` (без `IF NOT EXISTS`) | `CREATE TABLE IF NOT EXISTS suppliers (...)`<br>`CREATE TABLE IF NOT EXISTS products (...)` | Повторный запуск `init_db.py` с обычным `CREATE TABLE` падает: `OperationalError: table t already exists` (проверено). С `IF NOT EXISTS` скрипт безопасно запускается сколько угодно раз. |
| 2 | `cursor.execute(INSERT, FAKE_ROW)`<br>`conn.commit()`<br>`...`<br>`cursor.execute("DELETE FROM products WHERE supplier_id = 99999;")`<br>`conn.commit()` | `cursor.execute(INSERT, FAKE_ROW)`<br>`# commit() намеренно не вызываем`<br>`...`<br>`finally:`<br>`    conn.rollback()` | Без PRAGMA тестовая вставка в старой версии фиксировалась и затем удалялась вручную, но идентификатор при `AUTOINCREMENT` не освобождается: первый настоящий товар получал `id = 2` (проверено). `rollback()` не оставляет в БД никаких следов. |
| 3 | `price REAL NOT NULL`<br>`quantity INTEGER` | `quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0)`<br>`price REAL NOT NULL CHECK (price >= 0)` | Схема без `CHECK` принимает отрицательную цену (`INSERT -5.0` прошёл, проверено); с `CHECK` — `IntegrityError: CHECK constraint failed: price >= 0`. Правила предметной области защищены на уровне БД. |

Результаты проверок (реальный вывод):

```text
### ЛР8: CREATE TABLE без IF NOT EXISTS при повторном запуске
OperationalError: table t already exists

### ЛР8: схема без CHECK принимает отрицательную цену
вставлено: [(-5.0,)]
с CHECK: CHECK constraint failed: price >= 0

### ЛР8: commit в check_integrity без PRAGMA расходует AUTOINCREMENT id
id первой реальной записи: 2 (а не 1)

### Порядок создания таблиц: потомок раньше родителя
CREATE TABLE products (ссылка на ещё не созданную suppliers): выполнено без ошибки
INSERT в products до создания suppliers -> OperationalError: no such table: main.suppliers
после создания suppliers, но без поставщика 1 -> IntegrityError: FOREIGN KEY constraint failed

### Без commit() перед close()
строк после повторного открытия: 0 (изменение откатилось)
```

## Раздел 5. Ответы на контрольные вопросы

**1. Какая таблица родительская, какая дочерняя, где объявляется `REFERENCES` и почему `init_db.py` создаёт родительскую первой? Что будет при другом порядке?**
Родительская — `suppliers` (сторона «один»), дочерняя — `products` (сторона «многие»). `REFERENCES suppliers(id)` объявляется в дочерней таблице, в поле `supplier_id`. Родитель создаётся первым, потому что ссылка должна указывать на существующую таблицу: в большинстве СУБД иначе `CREATE TABLE` завершится ошибкой. В SQLite создание потомка раньше родителя проходит, но проверка выполняется при вставке: пока `suppliers` нет, `INSERT` в `products` падает с `no such table: main.suppliers`, а после создания родителя — с `FOREIGN KEY constraint failed`, если поставщика с таким `id` нет (проверено).

**2. Зачем `PRAGMA foreign_keys = ON;` и почему её выполняют после каждого подключения? Что будет, если забыть?**
Проверка внешних ключей в SQLite по умолчанию выключена (обратная совместимость). Это настройка *соединения*, а не файла БД, поэтому она не сохраняется и должна выполняться при каждом `connect`. Без неё вставка записи с несуществующим `supplier_id` проходит без ошибок — в БД появляется «осиротевшая» запись (проверено в `check_integrity.py`, пункт 2).

**3. Что означают элементы `PRAGMA table_info` (6) и `PRAGMA foreign_key_list` (8)? Как убедиться, что PK и FK настроены правильно?**
`table_info` → `(cid, name, type, notnull, dflt_value, pk)`: номер колонки, имя, тип, флаг NOT NULL, значение по умолчанию, признак первичного ключа (1 — входит в PK). `foreign_key_list` → `(id, seq, table, from, to, on_update, on_delete, match)`: номер ключа, номер колонки в составном ключе, родительская таблица, колонка потомка, колонка родителя, действия при изменении/удалении (по умолчанию `NO ACTION`), режим сопоставления. Проверка: у `id` обеих таблиц `pk = 1` (`(0, 'id', 'INTEGER', 0, None, 1)`), а во внешних ключах `products` есть `(0, 0, 'suppliers', 'supplier_id', 'id', 'NO ACTION', 'NO ACTION', 'NONE')`, то есть `supplier_id -> suppliers.id`.

**4. Почему `.db` выносится в `data/` и добавляется в `.gitignore`, но папка сохраняется через `.gitkeep`? Чем `data/` отличается от `data/*`?**
Файл БД — результат работы программы: он меняется, зависит от окружения и не является исходным кодом, поэтому его не коммитят, а хранят отдельно от кода. Git не хранит пустые папки, поэтому нужен файл-заглушка `.gitkeep`. Запись `data/` исключает папку целиком, и Git не заходит внутрь — исключение `!data/.gitkeep` не сработает. Запись `data/*` исключает только содержимое, и `!data/.gitkeep` возвращает заглушку (проверено настоящим `git ls-files`).

**5. Последовательность добавления одного «родителя» и двух связанных записей. Порядок вставок, зачем `commit()`, что будет без него перед `close()`?**

```sql
INSERT INTO suppliers (name) VALUES ('ИП Сидоров');                  -- 1) сначала родитель, получаем id (lastrowid)
INSERT INTO products (name, supplier_id) VALUES ('Сыр', 1);          -- 2) затем дочерние записи со ссылкой на него
INSERT INTO products (name, supplier_id) VALUES ('Масло', 1);
COMMIT;                                                               -- 3) фиксация транзакции
```

В Python: `cursor.execute("INSERT INTO suppliers ...", (...))`, `sid = cursor.lastrowid`, две вставки в `products` с `sid`, затем `conn.commit()`. Родитель вставляется первым, иначе `supplier_id` будет ссылаться на несуществующую запись. `commit()` фиксирует транзакцию; без него перед `close()` изменения откатываются и теряются (проверено: после повторного открытия таблица пуста, «строк: 0»).

## Раздел 6. Выводы

В работе я спроектировал структуру проекта и две связанные таблицы (поставщики и товары) и создал базу данных SQLite только средствами Python. Я понял, что внешние ключи в SQLite нужно включать в каждом соединении через `PRAGMA foreign_keys = ON`, и проверил на опыте, что без этого «осиротевшие» записи вставляются молча. Я научился читать структуру БД через `sqlite_master`, `PRAGMA table_info` и `PRAGMA foreign_key_list` и интерпретировать их кортежи. Неожиданностью стало поведение `AUTOINCREMENT`: даже откатанная или удалённая вставка расходует идентификатор, поэтому проверку целостности лучше завершать `rollback()`. Трудности вызвал `.gitignore` (папка `data/` против её содержимого), решение — `data/*` и `.gitkeep`. Самым полезным навыком считаю описание правил предметной области прямо в схеме (`NOT NULL`, `CHECK`, `REFERENCES`). Я понимаю код `init_db.py`, `check_db.py` и `check_integrity.py` и могу объяснить его построчно.
