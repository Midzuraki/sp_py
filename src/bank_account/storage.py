"""JSON-хранилище балансов счетов."""
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from src.bank_account.account import BankAccount
from src.core.config import DB_FILE


class JsonStorage:
    def __init__(self, file_path: Union[str, Path] = DB_FILE) -> None:
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            self.save_all({})

    def load_all(self) -> Dict[str, Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data: Dict[str, Dict[str, Any]] = json.load(f)
                return data
        except (json.JSONDecodeError, IOError):
            return {}

    def save_all(self, data: Dict[str, Any]) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_account(self, owner: str) -> Optional[BankAccount]:
        """Ищет аккаунт и восстанавливает только имя и текущий баланс."""
        db = self.load_all()
        if owner not in db:
            return None

        acc_data = db[owner]
        return BankAccount(owner, initial_balance=acc_data["balance"])

    def save_account(self, account: BankAccount) -> None:
        """Сохраняет исключительно актуальные сведения о балансе."""
        db = self.load_all()
        db[account.owner] = {"balance": account.balance}
        self.save_all(db)
