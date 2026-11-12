from pathlib import Path
BASE_DIR: Path = Path(__file__).resolve().parents[2]

LOG_DIR: Path = BASE_DIR / "logs"
LOG_FILE: Path = LOG_DIR / "app.log"
DB_FILE: Path = BASE_DIR / "accounts_db.json"
