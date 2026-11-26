from pathlib import Path
from library_app.library import Library
from library_app.models import (
    STATUS_READ,
    STATUS_READING,
    STATUS_UNREAD,
    Book,
)


def seed_data() -> None:
    data_dir = Path(__file__).resolve().parent / "data"

    for filename in ("books.json", "notes.txt", "stats.csv"):
        file_path = data_dir / filename
        if file_path.exists():
            file_path.unlink()

    library = Library(data_dir)

    books = [
        Book("Мастер и Маргарита", "Михаил Булгаков", 1967, "Классика", 480, STATUS_READ, 5),
        Book("Дюна", "Фрэнк Герберт", 1965, "Научная фантастика", 704, STATUS_READ, 5),
        Book("Кровь Кадии", "Джастин Д. Хилл", 2017, "Боевая фантастика", 384, STATUS_READ, 5),
        Book("Пикник на обочине", "Аркадий и Борис Стругацкие", 1972, "Фантастика", 256, STATUS_READING, None),
        Book("1984", "Джордж Оруэлл", 1949, "Антиутопия", 320, STATUS_READ, 4),
        Book("Ведьмак: Последнее желание", "Анджей Сапковский", 1993, "Фэнтези", 320, STATUS_UNREAD, None),
        Book("Чистый код", "Роберт Мартин", 2008, "Программирование", 464, STATUS_READING, None),
    ]

    for book in books:
        library.add_book(book)

    library.add_note("Кровь Кадии", "Кадия стояла до последнего! Отличная атмосфера Имперской Гвардии.")
    library.add_note("Дюна", "Не забыть дочитать приложения в конце книги.")
    library.add_note("Мастер и Маргарита", "Перечитать главы про Ершалаим.")

    library.add_month_stat("2026-09", 2, 800)
    library.add_month_stat("2026-10", 3, 1216)
    library.add_month_stat("2026-11", 1, 384)


if __name__ == "__main__":
    seed_data()
