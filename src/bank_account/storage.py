import json
import os
from src.bank_account.account import BankAccount


class JsonStorage:
    def __init__(self, file_path: str = "accounts_db.json") -> None:
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            self.save_all({})

    def load_all(self) -> dict[str, dict]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def save_all(self, data: dict) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_account(self, owner: str) -> BankAccount or None:
        """Ищет аккаунт и восстанавливает только имя и текущий баланс."""
        db = self.load_all()
        if owner not in db:
            return None

        acc_data = db[owner]
        return BankAccount(owner, initial_balance=acc_data["balance"])

    def save_account(self, account: BankAccount) -> None:
        """Сохраняет исключительно актуальные сведения о балансе."""
        db = self.load_all()
        db[account.owner] = {
            "balance": account.get_balance()
        }
        self.save_all(db)
