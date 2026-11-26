"""Работа с файлами, зачем оно так сделал спросите вы меня? А я не знаю, я дурак"""
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

PathLike = Union[str, Path]
ENCODING = "utf-8"
CSV_FIELDS = ["month", "books_read", "pages_read"]
NOTE_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\] «(.+?)»: (.*)$")


def _ensure_parent(filepath: PathLike) -> Path:
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


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


def append_note(
    filepath: PathLike, title: str, note: str, when: Optional[datetime] = None
) -> None:
    path = _ensure_parent(filepath)
    moment = (when or datetime.now()).strftime("%Y-%m-%d %H:%M")
    one_line = " ".join(note.split())
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
            if match:
                date, title, note = match.groups()
                notes.append({"date": date, "title": title, "note": note})
    return notes


def append_month_stat(
    filepath: PathLike, month: str, books_read: int, pages_read: int
) -> None:
    path = _ensure_parent(filepath)
    stats = read_stats(path)
    for row in stats:
        if row["month"] == month:
            row["books_read"] += books_read
            row["pages_read"] += pages_read
            break
    else:
        stats.append({"month": month, "books_read": books_read, "pages_read": pages_read})

    with open(path, "w", encoding=ENCODING, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(stats)


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
