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

    def add_book(self, book: Book) -> None:
        self.books.append(book)
        self.save()

    def remove_book(self, title: str) -> bool:
        before = len(self.books)
        self.books = [b for b in self.books if b.title.casefold() != title.casefold()]
        removed = len(self.books) != before
        if removed:
            self.save()
        return removed

    def get_book_by_title(self, title: str) -> Optional[Book]:
        needle = title.strip().casefold()
        if not needle:
            return None
        for book in self.books:
            if book.title.casefold() == needle:
                return book
        return None

    def find_by_author(self, author: str) -> List[Book]:
        needle = author.strip().casefold()
        if not needle:
            return []
        return [b for b in self.books if b.author.casefold().startswith(needle)]

    def find_by_genre(self, genre: str) -> List[Book]:
        needle = genre.strip().casefold()
        if not needle:
            return []
        return [b for b in self.books if b.genre.casefold().startswith(needle)]

    def find_by_title_prefix(self, prefix: str) -> List[Book]:
        needle = prefix.strip().casefold()
        if not needle:
            return []
        return [b for b in self.books if b.title.casefold().startswith(needle)]

    def save(self) -> None:
        storage.save_books_json([b.to_dict() for b in self.books], self.books_file)

    def load(self) -> None:
        self.books = [Book.from_dict(d) for d in storage.load_books_json(self.books_file)]

    def add_note(self, title: str, note: str) -> None:
        book = self.get_book_by_title(title)
        if book is None:
            raise ValueError(f"Книга «{title}» не найдена в библиотеке.")
        storage.append_note(self.notes_file, book.title, note)

    def get_notes(self, filter_title: Optional[str] = None) -> List[Dict[str, str]]:
        notes = storage.read_all_notes(self.notes_file)
        if filter_title is None:
            return notes
        return [n for n in notes if n["title"].casefold() == filter_title.casefold()]

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