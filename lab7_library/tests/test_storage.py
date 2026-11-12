"""Тесты модуля storage: JSON, TXT, CSV (все пути - во временной папке)."""
from datetime import datetime

from library_app import storage

# ---------- JSON ----------


def test_json_save_then_load_returns_same_data(tmp_path):
    data = [{"title": "Война и мир", "pages": 1225}, {"title": "Идиот", "pages": 640}]
    path = tmp_path / "books.json"
    storage.save_books_json(data, path)
    assert storage.load_books_json(path) == data


def test_json_load_missing_file_returns_empty_list(tmp_path):
    assert storage.load_books_json(tmp_path / "nope.json") == []


def test_json_cyrillic_saved_as_is(tmp_path):
    path = tmp_path / "books.json"
    storage.save_books_json([{"title": "Война и мир"}], path)
    text = path.read_text(encoding="utf-8")
    assert "Война и мир" in text
    assert "\\u" not in text


def test_json_save_creates_missing_folder(tmp_path):
    path = tmp_path / "a" / "b" / "books.json"
    storage.save_books_json([], path)
    assert path.exists()


# ---------- TXT ----------


def test_note_append_then_read(tmp_path):
    path = tmp_path / "notes.txt"
    storage.append_note(path, "Идиот", "Сильное начало", when=datetime(2026, 11, 12, 14, 30))
    assert path.read_text(encoding="utf-8") == "[2026-11-12 14:30] «Идиот»: Сильное начало\n"
    assert storage.read_all_notes(path) == [
        {"date": "2026-11-12 14:30", "title": "Идиот", "note": "Сильное начало"}
    ]


def test_several_notes_are_all_read(tmp_path):
    path = tmp_path / "notes.txt"
    for i in range(3):
        storage.append_note(path, f"Книга {i}", f"заметка {i}")
    notes = storage.read_all_notes(path)
    assert [n["title"] for n in notes] == ["Книга 0", "Книга 1", "Книга 2"]


def test_broken_note_lines_are_skipped(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text(
        "мусор без формата\n"
        "[2026-11-12 10:00] «Хорошая»: нормальная заметка\n"
        "[2026-11-12] «Без времени»: плохая дата\n"
        "\n",
        encoding="utf-8",
    )
    notes = storage.read_all_notes(path)
    assert len(notes) == 1
    assert notes[0]["title"] == "Хорошая"


def test_multiline_note_is_stored_in_one_line(tmp_path):
    path = tmp_path / "notes.txt"
    storage.append_note(path, "Т", "строка1\nстрока2")
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1


def test_read_notes_missing_file_returns_empty_list(tmp_path):
    assert storage.read_all_notes(tmp_path / "none.txt") == []


# ---------- CSV ----------


def test_csv_first_call_creates_file_with_header(tmp_path):
    path = tmp_path / "stats.csv"
    storage.append_month_stat(path, "2026-10", 2, 600)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "month,books_read,pages_read"
    assert lines[1] == "2026-10,2,600"


def test_csv_second_call_does_not_duplicate_header(tmp_path):
    path = tmp_path / "stats.csv"
    storage.append_month_stat(path, "2026-10", 2, 600)
    storage.append_month_stat(path, "2026-11", 1, 300)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines.count("month,books_read,pages_read") == 1
    assert len(lines) == 3


def test_csv_read_returns_ints(tmp_path):
    path = tmp_path / "stats.csv"
    storage.append_month_stat(path, "2026-10", 2, 600)
    row = storage.read_stats(path)[0]
    assert row == {"month": "2026-10", "books_read": 2, "pages_read": 600}
    assert isinstance(row["books_read"], int)
    assert isinstance(row["pages_read"], int)


def test_csv_read_missing_file_returns_empty_list(tmp_path):
    assert storage.read_stats(tmp_path / "none.csv") == []
