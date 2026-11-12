"""Бизнес-логика: класс Library. Сам с файлами не работает - зовёт модуль storage."""
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from library_app import storage
from library_app.models import Book


class Library:
    def __init__(self, data_dir: Union[str, Path]) -> None:
        self.data_dir = Path(data_dir)
        self.books_file = self.data_dir / "books.json"
        self.notes_file = self.data_dir / "notes.txt"
        self.stats_file = self.data_dir / "stats.csv"
        self.books: List[Book] = []

    # ----- книги -----
    def add_book(self, book: Book) -> None:
        self.books.append(book)
        self.save()  # сразу сохраняем

    def remove_book(self, title: str) -> bool:
        """Удаляет все книги с таким названием (без учёта регистра)."""
        before = len(self.books)
        self.books = [b for b in self.books if b.title.casefold() != title.casefold()]
        removed = len(self.books) != before
        if removed:
            self.save()
        return removed

    def find_by_author(self, author: str) -> List[Book]:
        needle = author.casefold()
        return [b for b in self.books if needle in b.author.casefold()]

    def find_by_genre(self, genre: str) -> List[Book]:
        needle = genre.casefold()
        return [b for b in self.books if needle in b.genre.casefold()]

    def save(self) -> None:
        storage.save_books_json([b.to_dict() for b in self.books], self.books_file)

    def load(self) -> None:
        """Загружает книги из JSON и восстанавливает объекты Book."""
        self.books = [Book.from_dict(d) for d in storage.load_books_json(self.books_file)]

    # ----- заметки -----
    def add_note(self, title: str, note: str) -> None:
        storage.append_note(self.notes_file, title, note)

    def get_notes(self, filter_title: Optional[str] = None) -> List[Dict[str, str]]:
        notes = storage.read_all_notes(self.notes_file)
        if filter_title is None:
            return notes
        return [n for n in notes if n["title"].casefold() == filter_title.casefold()]

    # ----- статистика -----
    def add_month_stat(self, month: str, books_read: int, pages_read: int) -> None:
        storage.append_month_stat(self.stats_file, month, books_read, pages_read)

    def get_stats(self) -> List[Dict[str, Any]]:
        return storage.read_stats(self.stats_file)

    def total_stats(self) -> Dict[str, int]:
        stats = self.get_stats()
        return {
            "books_read": sum(s["books_read"] for s in stats),
            "pages_read": sum(s["pages_read"] for s in stats),
        }
