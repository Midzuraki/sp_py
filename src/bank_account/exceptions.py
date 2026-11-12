"""Собственные исключения бизнес-логики банковского счета."""


class BankAccountError(Exception):
    """Базовое исключение: ловится одним `except` для всех ошибок счета."""


class NegativeInitialBalanceError(BankAccountError):
    """Отрицательный баланс при создании счета."""


class InvalidAmountError(BankAccountError):
    """Сумма операции не является строго положительной."""


class InsufficientFundsError(BankAccountError):
    """Недостаточно средств на счете для снятия."""
