"""Модель данных: класс Book."""
from typing import Any, Dict, Optional

STATUS_UNREAD = "не прочитана"
STATUS_READING = "читаю"
STATUS_READ = "прочитана"
STATUSES = (STATUS_UNREAD, STATUS_READING, STATUS_READ)


class Book:
    def __init__(
        self,
        title: str,
        author: str,
        year: int,
        genre: str,
        pages: int,
        status: str = STATUS_UNREAD,
        rating: Optional[int] = None,
    ) -> None:
        if status not in STATUSES:
            raise ValueError(f"Статус должен быть одним из: {', '.join(STATUSES)}")
        if rating is not None and not (isinstance(rating, int) and 1 <= rating <= 5):
            raise ValueError("Рейтинг должен быть целым числом от 1 до 5 или None")
        self.title = title
        self.author = author
        self.year = year
        self.genre = genre
        self.pages = pages
        self.status = status
        self.rating = rating

    def to_dict(self) -> Dict[str, Any]:
        """Объект -> словарь (для сохранения в JSON)."""
        return {
            "title": self.title,
            "author": self.author,
            "year": self.year,
            "genre": self.genre,
            "pages": self.pages,
            "status": self.status,
            "rating": self.rating,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Book":
        """Словарь -> объект. Отсутствующие status/rating получают значения по умолчанию."""
        return cls(
            title=data["title"],
            author=data["author"],
            year=data["year"],
            genre=data["genre"],
            pages=data["pages"],
            status=data.get("status", STATUS_UNREAD),
            rating=data.get("rating"),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return NotImplemented
        return self.to_dict() == other.to_dict()

    def __str__(self) -> str:
        text = f"«{self.title}» — {self.author} ({self.year}) [{self.status}]"
        if self.rating:
            text += " " + "★" * self.rating
        return text

    def __repr__(self) -> str:
        return f"Book({self.title!r}, {self.author!r}, {self.year!r}, ...)"
