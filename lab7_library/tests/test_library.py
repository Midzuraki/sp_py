"""Тесты класса Library."""
from library_app.library import Library
from library_app.models import Book


def test_add_book_persists_on_disk(library_with_books, data_dir, sample_book):
    reloaded = Library(data_dir)
    reloaded.load()
    assert sample_book in reloaded.books
    assert len(reloaded.books) == 2


def test_remove_book_returns_true_for_existing(library_with_books):
    assert library_with_books.remove_book("Война и мир") is True
    assert [b.title for b in library_with_books.books] == ["Мастер и Маргарита"]


def test_remove_book_is_saved_to_disk(library_with_books, data_dir):
    library_with_books.remove_book("Война и мир")
    reloaded = Library(data_dir)
    reloaded.load()
    assert len(reloaded.books) == 1


def test_remove_book_returns_false_for_missing(library_with_books):
    assert library_with_books.remove_book("Несуществующая") is False
    assert len(library_with_books.books) == 2


def test_find_by_author_is_case_insensitive_and_partial(library_with_books):
    assert [b.author for b in library_with_books.find_by_author("ТОЛСТ")] == ["Толстой"]
    assert library_with_books.find_by_author("толстой") == library_with_books.find_by_author("ТОЛСТОЙ")
    assert library_with_books.find_by_author("Пушкин") == []


def test_find_by_genre(library_with_books):
    assert len(library_with_books.find_by_genre("РОМАН")) == 2
    assert library_with_books.find_by_genre("поэма") == []


def test_get_notes_filter_returns_only_requested_book(empty_library):
    empty_library.add_note("Война и мир", "про Наташу")
    empty_library.add_note("Идиот", "про князя")
    empty_library.add_note("Война и мир", "про Пьера")
    assert len(empty_library.get_notes()) == 3
    filtered = empty_library.get_notes(filter_title="Война и мир")
    assert [n["note"] for n in filtered] == ["про Наташу", "про Пьера"]


def test_total_stats_sums_all_months(empty_library):
    empty_library.add_month_stat("2026-09", 2, 600)
    empty_library.add_month_stat("2026-10", 1, 450)
    empty_library.add_month_stat("2026-11", 3, 900)
    assert empty_library.total_stats() == {"books_read": 6, "pages_read": 1950}


def test_total_stats_empty_is_zero(empty_library):
    assert empty_library.total_stats() == {"books_read": 0, "pages_read": 0}


def test_load_on_empty_folder_does_not_fail(empty_library):
    empty_library.load()
    assert empty_library.books == []


def test_loaded_books_are_book_objects(library_with_books, data_dir):
    reloaded = Library(data_dir)
    reloaded.load()
    assert all(isinstance(b, Book) for b in reloaded.books)
