"""Работа с файлами: JSON (книги), TXT (заметки), CSV (статистика).

Здесь только функции и никаких «зашитых» путей: путь к файлу всегда приходит
параметром, поэтому тесты могут подсунуть временный файл.
"""
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

PathLike = Union[str, Path]
ENCODING = "utf-8"
CSV_FIELDS = ["month", "books_read", "pages_read"]
# [2026-11-12 14:30] «Название»: текст заметки
NOTE_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\] «(.+?)»: (.*)$")


def _ensure_parent(filepath: PathLike) -> Path:
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)  # папку создаём автоматически
    return path


# ---------- JSON ----------
def save_books_json(books_dicts: List[Dict[str, Any]], filepath: PathLike) -> None:
    path = _ensure_parent(filepath)
    with open(path, "w", encoding=ENCODING) as f:
        json.dump(books_dicts, f, ensure_ascii=False, indent=2)


def load_books_json(filepath: PathLike) -> List[Dict[str, Any]]:
    path = Path(filepath)
    if not path.exists():
        return []
    with open(path, "r", encoding=ENCODING) as f:
        data: List[Dict[str, Any]] = json.load(f)
        return data


# ---------- TXT ----------
def append_note(
    filepath: PathLike, title: str, note: str, when: Optional[datetime] = None
) -> None:
    path = _ensure_parent(filepath)
    moment = (when or datetime.now()).strftime("%Y-%m-%d %H:%M")
    one_line = " ".join(note.split())  # заметка всегда занимает одну строку
    with open(path, "a", encoding=ENCODING) as f:
        f.write(f"[{moment}] «{title}»: {one_line}\n")


def read_all_notes(filepath: PathLike) -> List[Dict[str, str]]:
    path = Path(filepath)
    if not path.exists():
        return []
    notes = []
    with open(path, "r", encoding=ENCODING) as f:
        for line in f:
            match = NOTE_RE.match(line.rstrip("\n"))
            if match:  # битые строки молча пропускаем
                date, title, note = match.groups()
                notes.append({"date": date, "title": title, "note": note})
    return notes


# ---------- CSV ----------
def append_month_stat(
    filepath: PathLike, month: str, books_read: int, pages_read: int
) -> None:
    path = _ensure_parent(filepath)
    need_header = not path.exists() or path.stat().st_size == 0
    with open(path, "a", encoding=ENCODING, newline="") as f:  # newline="" для Windows
        writer = csv.writer(f)
        if need_header:
            writer.writerow(CSV_FIELDS)
        writer.writerow([month, books_read, pages_read])


def read_stats(filepath: PathLike) -> List[Dict[str, Any]]:
    path = Path(filepath)
    if not path.exists():
        return []
    with open(path, "r", encoding=ENCODING, newline="") as f:
        return [
            {
                "month": row["month"],
                "books_read": int(row["books_read"]),  # числа - именно int
                "pages_read": int(row["pages_read"]),
            }
            for row in csv.DictReader(f)
        ]
