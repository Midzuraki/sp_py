# БД из двух связанных таблиц + CRUD (ЛР8–ЛР9)

**Вариант 3.** Товары (наименование, количество, цена, поставщик — один товар поставляет один
поставщик) и поставщики (название, менеджер, телефон). Нужно: выборка по поставщику и поиск по
названию товара. Работа ведётся только через Python-скрипты, SQLite (`sqlite3` — стандартная
библиотека, ничего устанавливать не нужно).

## Структура проекта

```
lab8_9_db/
├── .gitignore               # игнорирует .db, venv, кеши; папку data/ сохраняет
├── pyproject.toml           # метаданные, requires-python, build-system (pip install -e .)
├── README.md                # этот файл: структура, схема БД, API crud.py
├── data/
│   ├── .gitkeep             # заглушка, чтобы Git хранил пустую папку
│   └── myapp.db             # файл БД (результат работы init_db.py, в Git не попадает)
└── src/
    └── shop_db/             # весь код
        ├── __init__.py
        ├── config.py            # путь к БД по умолчанию (data/myapp.db)
        ├── init_db.py           # ТОЧКА ВХОДА: создаёт БД и две таблицы
        ├── check_db.py          # проверка структуры: PRAGMA и sqlite_master
        ├── check_integrity.py   # проверка ссылочной целостности (вставка с чужим parent_id)
        ├── seed_data.py         # наполнение тестовыми данными (executemany)       [ЛР9]
        ├── crud.py              # Create / Read / Update / Delete и поиск           [ЛР9]
        ├── demo_crud.py         # демонстрация всех функций crud.py на копии БД     [ЛР9]
        └── test_injection.py    # демонстрация SQL-инъекции на копии БД             [ЛР9]
```

### Обоснование структуры

* **Код в `src/shop_db/`, данные в `data/`.** Файл `.db` — результат работы скрипта, а не
  исходник: он меняется при каждом запуске и у каждого разработчика свой. Поэтому он лежит
  отдельно от кода и не коммитится (`data/*`, `*.db` в `.gitignore`).
* **Папка `data/` остаётся в репозитории через `.gitkeep`.** Git не хранит пустые папки. Запись
  `data/` в `.gitignore` исключает папку целиком, и «вернуть» файл правилом `!data/.gitkeep` уже
  нельзя — Git не заходит в игнорируемую папку. Запись `data/*` исключает только *содержимое*,
  поэтому `!data/.gitkeep` срабатывает, и после `git clone` папка на месте.
* **Путь к БД — параметр функций**, а не «зашитая» строка (значение по умолчанию — в `config.py`):
  скрипты можно запускать на копии БД, на временном файле или в тестах.
* **Каждый скрипт — отдельный модуль** с одной задачей: создать, проверить структуру, проверить
  целостность. `init_db.py` — точка входа (`python -m shop_db.init_db`).

## Определение таблиц и связи (ЛР8, шаг 3)

```
Родительская таблица:   suppliers (поставщики)
Дочерняя таблица:       products  (товары)
Поле-связка в дочерней: supplier_id INTEGER REFERENCES suppliers(id)
```

Связь «один ко многим»: у одного поставщика много товаров, у одного товара — один поставщик.

## Проектирование таблиц (ЛР8, шаг 4)

**Родительская таблица `suppliers`:**

| Имя поля | Тип | Ограничения | Назначение |
| --- | --- | --- | --- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный номер поставщика |
| name | TEXT | NOT NULL | Название поставщика |
| manager | TEXT | — | Менеджер, работающий с магазином |
| phone | TEXT | — | Контактный телефон |

**Дочерняя таблица `products`:**

| Имя поля | Тип | Ограничения | Назначение |
| --- | --- | --- | --- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный номер товара |
| name | TEXT | NOT NULL | Наименование товара |
| quantity | INTEGER | NOT NULL DEFAULT 0, CHECK (quantity >= 0) | Количество на складе |
| price | REAL | NOT NULL, CHECK (price >= 0) | Цена за единицу |
| supplier_id | INTEGER | NOT NULL, REFERENCES suppliers(id) | Ссылка на поставщика |

`supplier_id` объявлен `NOT NULL`: по условию варианта каждый товар обязательно имеет поставщика.

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e .                     # чтобы работал `python -m shop_db...` из любой папки

python -m shop_db.init_db            # создать БД и таблицы   -> data/myapp.db
python -m shop_db.check_db           # структура: PRAGMA table_info / foreign_key_list
python -m shop_db.check_integrity    # вставка с несуществующим supplier_id
python -m shop_db.seed_data          # тестовые данные (executemany)
python -m shop_db.demo_crud          # CRUD и поиск (на временной копии БД)
python -m shop_db.test_injection     # демонстрация SQL-инъекции (на копии БД)
```

## API модуля `crud.py` (ЛР9)

Первый параметр каждой функции — `db_path` (путь к файлу БД). Каждая функция сама открывает
соединение, включает `PRAGMA foreign_keys = ON`, делает `commit()` при изменении и закрывает
соединение. Все значения передаются через `?`.

| Функция | Параметры | Возвращает |
| --- | --- | --- |
| `add_supplier` | `db_path, name, manager=None, phone=None` | `id` новой записи (`lastrowid`) |
| `add_product` | `db_path, name, quantity, price, supplier_id` | `id` или `None`, если нарушено ограничение (нет поставщика, отрицательная цена) |
| `get_all` | `db_path, table_name` | список кортежей (`fetchall`) |
| `get_by_id` | `db_path, table_name, record_id` | кортеж или `None` (`fetchone`) |
| `select_products_by_supplier` | `db_path, supplier_id` | товары поставщика + название поставщика (JOIN) — выборка по варианту |
| `update_record` | `db_path, table_name, record_id, **fields` | `True`, если запись найдена и обновлена, иначе `False` (`rowcount`) |
| `delete_record` | `db_path, table_name, record_id` | `True`/`False`; `False`, если на запись ссылаются дочерние |
| `search_child_by_keyword` | `db_path, keyword` | товары, в названии которых есть `keyword` (без учёта регистра, включая кириллицу) |

**Безопасность.** Значения всегда идут через `?`. Имена таблиц и колонок (которые через `?`
передать нельзя) проверяются по белому списку `ALLOWED_COLUMNS`; неизвестное имя — `ValueError`.
В `LIKE` символ `%` добавляется к *значению* параметра, а пользовательские `%` и `_`
экранируются. SQLite сравнивает регистр через `LIKE` только для латиницы, поэтому для поиска по
кириллице регистрируется функция `PYLOWER` (`str.casefold`).
