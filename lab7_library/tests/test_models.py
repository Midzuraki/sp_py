from datetime import datetime
import pytest

from library_app.models import Book


def test_to_dict_returns_correct_dict(sample_book):
    """Преобразование книги в словарь возвращает все поля в правильном формате."""
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
    """Книга корректно восстанавливается из словаря и является новым объектом."""
    restored = Book.from_dict(sample_book.to_dict())
    assert restored == sample_book
    assert restored is not sample_book


def test_defaults_status_and_rating():
    """По умолчанию новая книга получает статус 'не прочитана' и рейтинг None."""
    book = Book("Т", "А", 2000, "ж", 100)
    assert book.status == "не прочитана"
    assert book.rating is None


def test_from_dict_without_optional_fields_uses_defaults():
    """При загрузке из словаря без статуса и оценки подставляются значения по умолчанию."""
    book = Book.from_dict(
        {"title": "Т", "author": "А", "year": 2000, "genre": "ж", "pages": 100}
    )
    assert book.status == "не прочитана"
    assert book.rating is None


def test_eq_different_books_are_not_equal(sample_book):
    """Разные книги или объекты других типов не считаются равными."""
    assert sample_book != Book("Другая", "Автор", 2000, "жанр", 10)
    assert sample_book != "не книга"


def test_str_format_with_full_stars(sample_book):
    """Строковое представление книги с оценкой 5 выводит пять закрашенных звёзд."""
    assert str(sample_book) == "«Война и мир» — Толстой (1869) [прочитана] ★★★★★"


def test_str_format_with_empty_stars():
    """Строковое представление книги с оценкой 3 дополняется двумя пустыми звёздами."""
    book = Book("Т", "А", 2000, "ж", 100, status="прочитана", rating=3)
    assert str(book) == "«Т» — А (2000) [прочитана] ★★★☆☆"


def test_str_without_rating():
    """Строковое представление книги без оценки не содержит звёзд."""
    assert str(Book("Т", "А", 2000, "ж", 100)) == "«Т» — А (2000) [не прочитана]"


@pytest.mark.parametrize("bad_rating", [0, 6, -1, "5", 4.5, True])
def test_invalid_rating_raises_value_error(bad_rating):
    """Некорректная оценка (не число от 1 до 5) вызывает ValueError."""
    with pytest.raises(ValueError):
        Book("Т", "А", 2000, "ж", 100, status="прочитана", rating=bad_rating)


@pytest.mark.parametrize("bad_status", ["не прочитана", "читаю"])
def test_rating_for_unread_book_raises_value_error(bad_status):
    """Попытка поставить оценку непрочитанной книге вызывает ValueError."""
    with pytest.raises(ValueError):
        Book("Т", "А", 2000, "ж", 100, status=bad_status, rating=5)


@pytest.mark.parametrize("bad_year", [0, -100, datetime.now().year + 1, "2020", True])
def test_invalid_year_raises_value_error(bad_year):
    """Год издания меньше 1, из будущего или не число вызывает ValueError."""
    with pytest.raises(ValueError):
        Book("Т", "А", bad_year, "ж", 100)


def test_invalid_status_raises_value_error():
    """Несуществующий статус книги вызывает ValueError."""
    with pytest.raises(ValueError):
        Book("Т", "А", 2000, "ж", 100, status="на полке")