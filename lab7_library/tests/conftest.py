"""Общие фикстуры. Тесты работают только во временной папке tmp_path, не в data/."""
import pytest

from library_app.library import Library
from library_app.models import Book


@pytest.fixture
def data_dir(tmp_path):
    """Временная папка для данных (путь ещё не создан - библиотека создаст сама)."""
    return tmp_path / "data"


@pytest.fixture
def empty_library(data_dir):
    return Library(data_dir)


@pytest.fixture
def sample_book():
    return Book("Война и мир", "Толстой", 1869, "роман", 1225, "прочитана", 5)


@pytest.fixture
def library_with_books(empty_library, sample_book):
    empty_library.add_book(sample_book)
    empty_library.add_book(Book("Мастер и Маргарита", "Булгаков", 1967, "роман", 480))
    return empty_library
