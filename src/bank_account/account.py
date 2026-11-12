"""Класс BankAccount: бизнес-логика счета, валидация и логирование операций."""
import logging

from src.bank_account.exceptions import (
    InsufficientFundsError,
    InvalidAmountError,
    NegativeInitialBalanceError,
)
from src.core.config import LOG_DIR, LOG_FILE

# Настройка логирования: все события пишутся в logs/app.log
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")],
)
logger = logging.getLogger("BankAccount")


class BankAccount:
    bank_name: str = "Центральный Банк"

    def __init__(self, owner: str, initial_balance: float = 0.0) -> None:
        if initial_balance < 0:
            logger.error(
                f"Попытка создания счета с отрицательным балансом: "
                f"{initial_balance} для {owner}"
            )
            raise NegativeInitialBalanceError(
                f"Отрицательный баланс: {initial_balance}"
            )

        self._owner: str = owner
        self._balance: float = initial_balance
        logger.info(f"Создан счет для {owner} с балансом {initial_balance} руб.")

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            logger.warning(f"[{self.owner}] Некорректная сумма пополнения: {amount}")
            raise InvalidAmountError(f"Сумма должна быть > 0: {amount}")

        self._balance += amount
        logger.info(
            f"[{self.owner}] Пополнение: +{amount} руб. "
            f"Текущий баланс: {self._balance} руб."
        )

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            logger.warning(f"[{self.owner}] Некорректная сумма снятия: {amount}")
            raise InvalidAmountError(f"Сумма должна быть > 0: {amount}")

        if amount > self._balance:
            logger.error(
                f"[{self.owner}] Отказ в снятии {amount} руб. "
                f"Недостаточно средств (баланс: {self._balance})"
            )
            raise InsufficientFundsError(
                f"Нельзя выдать {amount:.2f}, баланс {self._balance:.2f}"
            )

        self._balance -= amount
        logger.info(
            f"[{self.owner}] Снятие: -{amount} руб. "
            f"Текущий баланс: {self._balance} руб."
        )

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def owner(self) -> str:
        return self._owner

    def __str__(self) -> str:
        """Человекочитаемое представление (для пользователя)."""
        return f"Счет ({self.owner}) | Текущий баланс: {self._balance:.2f} руб."

    def __repr__(self) -> str:
        """Однозначное представление (для разработчика и отладки)."""
        return (
            f"BankAccount(owner={self._owner!r}, initial_balance={self._balance!r})"
        )
