"""Консольное меню. Вся логика данных - в Library, здесь только ввод/вывод."""
import os
from pathlib import Path
from typing import Callable, List, Optional

from library_app.library import Library
from library_app.models import STATUS_READ, STATUS_READING, STATUS_UNREAD, Book

# .../src/library_app/cli.py -> корень проекта -> data/ (можно переопределить переменной)
DEFAULT_DATA_DIR = Path(
    os.environ.get("LIBRARY_DATA_DIR", Path(__file__).resolve().parents[2] / "data")
)

MENU = """
=== ЛИЧНАЯ БИБЛИОТЕКА ===
1. Добавить книгу
2. Показать все книги
3. Найти по автору
4. Найти по жанру
5. Добавить заметку
6. Показать заметки
7. Добавить статистику за месяц
8. Показать общую статистику
9. Удалить книгу
0. Выход"""

STATUS_CHOICES = {"1": STATUS_UNREAD, "2": STATUS_READING, "3": STATUS_READ}


class UserInterface:
    """Ввод и вывод передаются параметрами - так меню можно проверить без клавиатуры."""

    def __init__(
        self,
        library: Library,
        input_func: Callable[[str], str] = input,
        output_func: Callable[[str], None] = print,
    ) -> None:
        self.library = library
        self.ask = input_func
        self.say = output_func

    # ----- безопасный ввод -----
    def ask_text(self, prompt: str) -> str:
        while True:
            value = self.ask(prompt).strip()
            if value:
                return value
            self.say("Ошибка: строка не может быть пустой.")

    def ask_int(self, prompt: str, minimum: Optional[int] = None) -> int:
        while True:
            try:
                value = int(self.ask(prompt).strip())
            except ValueError:
                self.say("Ошибка: введите целое число.")
                continue
            if minimum is not None and value < minimum:
                self.say(f"Ошибка: число должно быть не меньше {minimum}.")
                continue
            return value

    def show_books(self, books: List[Book]) -> None:
        if not books:
            self.say("Ничего не найдено.")
        for number, book in enumerate(books, start=1):
            self.say(f"{number}. {book}")

    # ----- пункты меню -----
    def add_book(self) -> None:
        title = self.ask_text("Название: ")
        author = self.ask_text("Автор: ")
        year = self.ask_int("Год издания: ", minimum=1)
        genre = self.ask_text("Жанр: ")
        pages = self.ask_int("Количество страниц: ", minimum=1)
        self.say("Статус: 1 - не прочитана, 2 - читаю, 3 - прочитана")
        status = STATUS_CHOICES.get(self.ask("Выберите статус (Enter = 1): ").strip(), STATUS_UNREAD)
        rating: Optional[int] = None
        raw_rating = self.ask("Оценка 1-5 (Enter - без оценки): ").strip()
        if raw_rating:
            try:
                rating = int(raw_rating)
            except ValueError:
                self.say("Оценка не распознана - книга сохранена без оценки.")
        try:
            self.library.add_book(Book(title, author, year, genre, pages, status, rating))
        except ValueError as error:  # неверный статус/рейтинг
            self.say(f"Ошибка: {error}")
            return
        self.say("Книга добавлена.")

    def add_note(self) -> None:
        self.library.add_note(self.ask_text("Название книги: "), self.ask_text("Заметка: "))
        self.say("Заметка сохранена.")

    def show_notes(self) -> None:
        title = self.ask("Название книги (Enter - все заметки): ").strip() or None
        notes = self.library.get_notes(title)
        if not notes:
            self.say("Заметок нет.")
        for note in notes:
            self.say(f"[{note['date']}] «{note['title']}»: {note['note']}")

    def add_month_stat(self) -> None:
        month = self.ask_text("Месяц (например, 2026-11): ")
        books = self.ask_int("Прочитано книг: ", minimum=0)
        pages = self.ask_int("Прочитано страниц: ", minimum=0)
        self.library.add_month_stat(month, books, pages)
        self.say("Статистика сохранена.")

    def show_total_stats(self) -> None:
        total = self.library.total_stats()
        for row in self.library.get_stats():
            self.say(f"{row['month']}: книг {row['books_read']}, страниц {row['pages_read']}")
        self.say(f"ВСЕГО: книг {total['books_read']}, страниц {total['pages_read']}")

    def remove_book(self) -> None:
        title = self.ask_text("Название книги для удаления: ")
        if self.library.remove_book(title):
            self.say("Книга удалена.")
        else:
            self.say("Книга с таким названием не найдена.")

    def loop(self) -> None:
        actions = {
            "1": self.add_book,
            "2": lambda: self.show_books(self.library.books),
            "3": lambda: self.show_books(
                self.library.find_by_author(self.ask_text("Автор (или часть): "))
            ),
            "4": lambda: self.show_books(
                self.library.find_by_genre(self.ask_text("Жанр (или часть): "))
            ),
            "5": self.add_note,
            "6": self.show_notes,
            "7": self.add_month_stat,
            "8": self.show_total_stats,
            "9": self.remove_book,
        }
        while True:
            self.say(MENU)
            choice = self.ask("Выберите пункт: ").strip()
            if choice == "0":
                return
            action = actions.get(choice)
            if action is None:
                self.say("Неверный пункт меню.")
                continue
            action()


def run(data_dir: Optional[Path] = None) -> None:
    """Запуск приложения: загрузка -> меню -> сохранение при выходе."""
    library = Library(data_dir or DEFAULT_DATA_DIR)
    library.load()
    ui = UserInterface(library)
    try:
        ui.loop()
    except (KeyboardInterrupt, EOFError):
        print("\nПрервано пользователем.")
    finally:
        library.save()  # при выходе - всегда сохраняем
        print("Данные сохранены. До свидания!")
