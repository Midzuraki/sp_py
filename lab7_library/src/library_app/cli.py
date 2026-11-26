from datetime import datetime
import os
from pathlib import Path
import re
from typing import Callable, List, Optional

from library_app.library import Library
from library_app.models import STATUS_READ, STATUS_READING, STATUS_UNREAD, Book

DEFAULT_DATA_DIR = Path(
    os.environ.get("LIBRARY_DATA_DIR", Path(__file__).resolve().parents[2] / "data")
)

MENU = """
=== meow ===
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

    def __init__(
        self,
        library: Library,
        input_func: Callable[[str], str] = input,
        output_func: Callable[[str], None] = print,
    ) -> None:
        self.library = library
        self.ask = input_func
        self.say = output_func

    def ask_text(self, prompt: str) -> str:
        while True:
            value = self.ask(prompt).strip()
            if value:
                return value
            self.say("Ошибка: строка не может быть пустой.")

    def ask_int(
        self, prompt: str, minimum: Optional[int] = None, maximum: Optional[int] = None
    ) -> int:
        while True:
            try:
                value = int(self.ask(prompt).strip())
            except ValueError:
                self.say("Ошибка: введите целое число.")
                continue
            if minimum is not None and value < minimum:
                self.say(f"Ошибка: число должно быть не меньше {minimum}.")
                continue
            if maximum is not None and value > maximum:
                self.say(f"Ошибка: число должно быть не больше {maximum}.")
                continue
            return value

    def ask_status(self) -> str:
        self.say("Статус: 1 - не прочитана, 2 - читаю, 3 - прочитана")
        while True:
            raw = self.ask("Выберите статус (Enter = 1): ").strip()
            if not raw:
                return STATUS_UNREAD
            if raw in STATUS_CHOICES:
                return STATUS_CHOICES[raw]
            self.say("Ошибка: введите 1, 2, 3 или нажмите Enter.")

    def ask_rating(self) -> Optional[int]:
        while True:
            raw = self.ask("Оценка 1-5 (Enter - без оценки): ").strip()
            if not raw:
                return None
            try:
                value = int(raw)
                if 1 <= value <= 5:
                    return value
            except ValueError:
                pass
            self.say("Ошибка: введите целое число от 1 до 5 или нажмите Enter.")

    def ask_month(self, prompt: str) -> str:
        current_month = datetime.now().strftime("%Y-%m")
        while True:
            value = self.ask(prompt).strip()
            if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value) or value.startswith("0000"):
                self.say("Ошибка: введите месяц в формате ГГГГ-ММ (например, 2000-01).")
                continue
            if value > current_month:
                self.say(f"Ошибка: месяц не может быть больше текущего ({current_month}).")
                continue
            return value

    def show_books(self, books: List[Book]) -> None:
        if not books:
            self.say("Ничего не найдено.")
        for number, book in enumerate(books, start=1):
            self.say(f"{number}. {book}")

    def add_book(self) -> None:
        while True:
            title = self.ask_text("Название: ")
            author = self.ask_text("Автор: ")
            current_year = datetime.now().year
            year = self.ask_int("Год издания: ", minimum=1, maximum=current_year)
            genre = self.ask_text("Жанр: ")
            pages = self.ask_int("Количество страниц: ", minimum=1)
            status = self.ask_status()
            rating = self.ask_rating() if status == STATUS_READ else None
            try:
                self.library.add_book(Book(title, author, year, genre, pages, status, rating))
                break
            except ValueError as error:
                self.say(f"Ошибка: {error}. Попробуйте снова.")
        self.say("Книга добавлена.")

    def add_note(self) -> None:
        while True:
            title = self.ask("Название книги (Enter - выход): ").strip()
            if not title:
                return
            book = self.library.get_book_by_title(title)
            if book is not None:
                break
            self.say("Ошибка: книга с таким названием не найдена. Попробуйте снова.")

        note = self.ask_text("Заметка: ")
        self.library.add_note(book.title, note)
        self.say("Заметка сохранена.")

    def show_notes(self) -> None:
        title = self.ask("Название книги (Enter - все заметки): ").strip() or None
        notes = self.library.get_notes(title)
        if not notes:
            self.say("Заметок нет.")
        for note in notes:
            self.say(f"[{note['date']}] «{note['title']}»: {note['note']}")

    def add_month_stat(self) -> None:
        month = self.ask_month("Месяц (например, 2026-11): ")
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
        self.show_books(self.library.books)
        if not self.library.books:
            return
        while True:
            title = self.ask("Название книги для удаления (Enter - выход): ").strip()
            if not title:
                return
            book = self.library.get_book_by_title(title)
            if book is not None:
                break
            self.say("Ошибка: книга с таким названием не найдена. Попробуйте снова.")

        while True:
            confirm = self.ask(f'Вы точно хотите удалить книгу "{book.title}"? (y/n): ').strip().lower()
            if confirm == "y":
                self.library.remove_book(book.title)
                self.say("Книга удалена.")
                return
            if confirm == "n":
                self.say("Удаление отменено.")
                return
            self.say("Ошибка: введите y или n.")

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
    library = Library(data_dir or DEFAULT_DATA_DIR)
    library.load()
    ui = UserInterface(library)
    try:
        ui.loop()
    except (KeyboardInterrupt, EOFError):
        print("\nПрервано пользователем.")
    finally:
        library.save()
        print("Данные сохранены. До свидания!")