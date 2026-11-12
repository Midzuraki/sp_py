"""Путь к файлу БД по умолчанию: <корень проекта>/data/myapp.db."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "myapp.db"
