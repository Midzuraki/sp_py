"""Демонстрация CRUD и поиска на временной копии БД (запуск: python -m shop_db.demo_crud)."""
import shutil
import tempfile
from pathlib import Path

from shop_db import crud
from shop_db.config import DEFAULT_DB_PATH
from shop_db.seed_data import seed


def main() -> None:
    if not Path(DEFAULT_DB_PATH).exists():
        seed()
    workdir = Path(tempfile.mkdtemp())
    db = workdir / "demo.db"
    shutil.copy(DEFAULT_DB_PATH, db)

    print("== Create ==")
    sid = crud.add_supplier(db, "ООО «Рыбком»", "Кузнецов Д.А.", "+7 900 555-66-77")
    print("add_supplier ->", sid)
    pid = crud.add_product(db, "Сёмга охлаждённая", 25, 1450.0, sid)
    print("add_product ->", pid)
    print("add_product с несуществующим поставщиком ->", crud.add_product(db, "Призрак", 1, 1.0, 999))
    print("add_product с отрицательной ценой ->", crud.add_product(db, "Брак", 1, -5.0, sid))

    print("\n== Read ==")
    print("get_all(suppliers):")
    for row in crud.get_all(db, "suppliers"):
        print("  ", row)
    print("get_by_id(products, 1) ->", crud.get_by_id(db, "products", 1))
    print("get_by_id(products, 9999) ->", crud.get_by_id(db, "products", 9999))
    print("Товары поставщика 1:")
    for row in crud.select_products_by_supplier(db, 1):
        print("  ", row)

    print("\n== Update ==")
    print("update_record(products, 1, price=84.9, quantity=100) ->",
          crud.update_record(db, "products", 1, price=84.9, quantity=100))
    print("  после:", crud.get_by_id(db, "products", 1))
    print("update_record(products, 9999, price=1) ->", crud.update_record(db, "products", 9999, price=1))
    print("update_record(products, 1, supplier_id=777) ->", crud.update_record(db, "products", 1, supplier_id=777))
    try:
        crud.update_record(db, "products", 1, **{"price = 0, name": "взлом"})
    except ValueError as error:
        print("update_record с «опасным» именем поля ->", error)

    print("\n== Search ==")
    print("'ок'     ->", [r[1] for r in crud.search_child_by_keyword(db, "ок")])
    print("'ХЛЕБ'   ->", [r[1] for r in crud.search_child_by_keyword(db, "ХЛЕБ")])
    print("''       -> найдено", len(crud.search_child_by_keyword(db, "")), "из", len(crud.get_all(db, "products")))
    print("'zzz'    ->", crud.search_child_by_keyword(db, "zzz"))
    print("'%'      ->", crud.search_child_by_keyword(db, "%"), "(% экранирован: найдены только названия с символом %)")

    print("\n== Delete ==")
    print("delete_record(suppliers, 1) (есть товары) ->", crud.delete_record(db, "suppliers", 1))
    for p in crud.select_products_by_supplier(db, 1):
        crud.delete_record(db, "products", p[0])
    print("после удаления товаров: delete_record(suppliers, 1) ->", crud.delete_record(db, "suppliers", 1))
    print("delete_record(suppliers, 1) ещё раз ->", crud.delete_record(db, "suppliers", 1))

    shutil.rmtree(workdir)


if __name__ == "__main__":
    main()
