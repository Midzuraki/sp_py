import logging
import os
from src.bank_account.exceptions import (
    NegativeInitialBalanceError,
    InvalidAmountError,
    InsufficientFundsError
)

# Настройка логирования (только в файл logs/app.log с временной меткой)
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("BankAccount")


class BankAccount:
    bank_name: str = "Центральный Банк"

    def __init__(self, owner: str, initial_balance: float = 0.0) -> None:
        if initial_balance < 0:
            logger.error(f"Попытка создания счета с отрицательным балансом: {initial_balance} для {owner}")
            raise NegativeInitialBalanceError(f"Отрицательный баланс: {initial_balance}")

        self.owner: str = owner
        self._balance: float = initial_balance
        logger.info(f"Создан счет для {owner} с балансом {initial_balance} руб.")

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            logger.warning(f"[{self.owner}] Некорректная сумма пополнения: {amount}")
            raise InvalidAmountError(f"Сумма должна быть > 0: {amount}")

        self._balance += amount
        logger.info(f"[{self.owner}] Пополнение: +{amount} руб. Текущий баланс: {self._balance} руб.")

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            logger.warning(f"[{self.owner}] Некорректная сумма снятия: {amount}")
            raise InvalidAmountError(f"Сумма должна быть > 0: {amount}")

        if amount > self._balance:
            logger.warning(
                f"[{self.owner}] Отказ в снятии {amount} руб. Недостаточно средств (баланс: {self._balance})")
            raise InsufficientFundsError(f"Недостаточно средств. Баланс: {self._balance}")

        self._balance -= amount
        logger.info(f"[{self.owner}] Снятие: -{amount} руб. Текущий баланс: {self._balance} руб.")

    def get_balance(self) -> float:
        return self._balance

    def __str__(self) -> str:
        return f"Счет ({self.owner}) | Текущий баланс: {self._balance:.2f} руб."
