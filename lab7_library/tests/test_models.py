"""Тесты модели Book."""
import pytest

from library_app.models import Book


def test_to_dict_returns_correct_dict(sample_book):
    assert sample_book.to_dict() == {
        "title": "Война и мир",
        "author": "Толстой",
        "year": 1869,
        "genre": "роман",
        "pages": 1225,
        "status": "прочитана",
        "rating": 5,
    }


def test_from_dict_round_trip(sample_book):
    restored = Book.from_dict(sample_book.to_dict())
    assert restored == sample_book
    assert restored is not sample_book


def test_defaults_status_and_rating():
    book = Book("Т", "А", 2000, "ж", 100)
    assert book.status == "не прочитана"
    assert book.rating is None


def test_from_dict_without_optional_fields_uses_defaults():
    book = Book.from_dict(
        {"title": "Т", "author": "А", "year": 2000, "genre": "ж", "pages": 100}
    )
    assert book.status == "не прочитана"
    assert book.rating is None


def test_eq_different_books_are_not_equal(sample_book):
    assert sample_book != Book("Другая", "Автор", 2000, "жанр", 10)
    assert sample_book != "не книга"


def test_str_format(sample_book):
    assert str(sample_book) == "«Война и мир» — Толстой (1869) [прочитана] ★★★★★"


def test_str_without_rating():
    assert str(Book("Т", "А", 2000, "ж", 100)) == "«Т» — А (2000) [не прочитана]"


@pytest.mark.parametrize("bad_rating", [0, 6, -1, "5", 4.5])
def test_invalid_rating_raises_value_error(bad_rating):
    with pytest.raises(ValueError):
        Book("Т", "А", 2000, "ж", 100, rating=bad_rating)


def test_invalid_status_raises_value_error():
    with pytest.raises(ValueError):
        Book("Т", "А", 2000, "ж", 100, status="на полке")
