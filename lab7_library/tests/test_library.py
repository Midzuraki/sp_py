from library_app.library import Library
from library_app.models import Book


def test_book_is_saved_to_disk_after_adding(library_with_books, data_dir, sample_book):
    """Добавленная книга сохраняется на диск и загружается обратно."""
    reloaded = Library(data_dir)
    reloaded.load()
    assert sample_book in reloaded.books
    assert len(reloaded.books) == 2


def test_remove_existing_book_returns_true(library_with_books):
    """Удаление существующей книги возвращает True и убирает её из списка."""
    assert library_with_books.remove_book("Война и мир") is True
    assert [b.title for b in library_with_books.books] == ["Мастер и Маргарита"]


def test_book_removal_persists_on_disk(library_with_books, data_dir):
    """Удаление книги сразу сохраняется в файл books.json."""
    library_with_books.remove_book("Война и мир")
    reloaded = Library(data_dir)
    reloaded.load()
    assert len(reloaded.books) == 1


def test_search_by_author_ignores_case_and_matches_prefix(library_with_books):
    """Поиск по автору работает только с начала строки и без учёта регистра."""
    assert [b.author for b in library_with_books.find_by_author("ТОЛСТ")] == ["Толстой"]
    assert library_with_books.find_by_author("толстой") == library_with_books.find_by_author("ТОЛСТОЙ")
    assert library_with_books.find_by_author("стой") == []
    assert library_with_books.find_by_author("Пушкин") == []


def test_search_by_genre_ignores_case_and_matches_prefix(library_with_books):
    """Поиск по жанру находит совпадения только с начала строки независимо от регистра."""
    assert len(library_with_books.find_by_genre("РОМ")) == 2
    assert library_with_books.find_by_genre("ман") == []
    assert library_with_books.find_by_genre("поэма") == []



def test_search_by_title_prefix_ignores_empty_or_spaces(library_with_books):
    """Пустой запрос или запрос из пробелов возвращает пустой список."""
    assert library_with_books.find_by_title_prefix("") == []
    assert library_with_books.find_by_title_prefix("   ") == []


def test_filter_notes_by_book_title(empty_library):
    """Фильтрация заметок возвращает записи только для указанной книги."""
    empty_library.add_note("Война и мир", "про Наташу")
    empty_library.add_note("Идиот", "про князя")
    empty_library.add_note("Война и мир", "про Пьера")
    assert len(empty_library.get_notes()) == 3
    filtered = empty_library.get_notes(filter_title="Война и мир")
    assert [n["note"] for n in filtered] == ["про Наташу", "про Пьера"]


def test_total_stats_sums_all_months(empty_library):
    """Общая статистика корректно суммирует книги и страницы за все месяцы."""
    empty_library.add_month_stat("2026-09", 2, 600)
    empty_library.add_month_stat("2026-10", 1, 450)
    empty_library.add_month_stat("2026-11", 3, 900)
    assert empty_library.total_stats() == {"books_read": 6, "pages_read": 1950}


def test_same_month_stats_are_merged(empty_library):
    """Повторное добавление статистики за тот же месяц суммирует показатели без дублей."""
    empty_library.add_month_stat("2026-10", 1, 400)
    empty_library.add_month_stat("2026-10", 2, 500)
    stats = empty_library.get_stats()
    assert len(stats) == 1
    assert stats[0] == {"month": "2026-10", "books_read": 3, "pages_read": 900}


def test_total_stats_for_empty_library_is_zero(empty_library):
    """Для пустой библиотеки общая статистика равна нулю."""
    assert empty_library.total_stats() == {"books_read": 0, "pages_read": 0}


def test_load_from_empty_folder_does_not_fail(empty_library):
    """Загрузка из пустой папки не вызывает ошибок и оставляет список книг пустым."""
    empty_library.load()
    assert empty_library.books == []


def test_loaded_items_are_book_instances(library_with_books, data_dir):
    """После загрузки из JSON все элементы списка являются объектами Book."""
    reloaded = Library(data_dir)
    reloaded.load()
    assert all(isinstance(b, Book) for b in reloaded.books)
