"""ЛР1: класс BankAccount с инкапсуляцией (первая рабочая версия + рефакторинг)."""


class BankAccount:
    bank_name = "Центральный Банк"  # атрибут класса: общий для всех счетов

    def __init__(self, owner: str, initial_balance: float = 0.0) -> None:
        if initial_balance < 0:
            raise ValueError("Начальный баланс не может быть отрицательным")
        self.owner = owner
        self._balance = float(initial_balance)  # приватный атрибут экземпляра
        self._transactions: list = []  # история операций

    def _add_transaction(self, operation_type: str, amount: float) -> None:
        """Приватный метод: историю пишет только сам класс."""
        self._transactions.append(
            {
                "type": operation_type,
                "amount": amount,
                "balance_after": self._balance,
            }
        )

    def deposit(self, amount: float) -> None:
        """Пополнение счета: сумма должна быть строго положительной."""
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self._balance += amount
        self._add_transaction("Пополнение", amount)

    def withdraw(self, amount: float) -> None:
        """Снятие: нельзя снять неположительную сумму или уйти в минус."""
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        if amount > self._balance:
            raise ValueError(
                f"Недостаточно средств для снятия {amount:g} руб. "
                f"(доступно: {self._balance:g})"
            )
        self._balance -= amount
        self._add_transaction("Снятие", amount)

    def get_balance(self) -> float:
        """Геттер баланса (читать _balance напрямую не нужно)."""
        return self._balance

    def get_transactions(self) -> list:
        """Геттер возвращает КОПИЮ истории, чтобы её нельзя было испортить извне."""
        return self._transactions.copy()

    def __str__(self) -> str:
        return f"Счет {self.owner}: {self._balance:g} руб. ({self.bank_name})"
