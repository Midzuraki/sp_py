"""Тесты класса BankAccount (ЛР3): фикстуры, параметризация, маркеры."""
import pytest

from src.bank_account.account import BankAccount
from src.bank_account.exceptions import (
    BankAccountError,
    InsufficientFundsError,
    InvalidAmountError,
    NegativeInitialBalanceError,
)

# =====================================================================
# БЛОК 1: Создание счета (3 обязательных теста)
# =====================================================================


@pytest.mark.smoke
def test_create_account_positive_balance():
    """Позитивный баланс при создании."""
    account = BankAccount(owner="Ivan", initial_balance=500.0)
    assert account.balance == 500.0


def test_create_account_zero_balance(empty_account):
    """Нулевой баланс при создании."""
    assert empty_account.balance == 0.0


@pytest.mark.regression
def test_create_account_negative_balance_raises_error():
    """Отрицательный баланс при создании (ошибка)."""
    with pytest.raises(NegativeInitialBalanceError, match="Отрицательный баланс"):
        BankAccount(owner="Ivan", initial_balance=-100.0)


# =====================================================================
# БЛОК 2: Пополнение счета (2 обязательных теста + параметризация)
# =====================================================================


@pytest.mark.smoke
@pytest.mark.parametrize(
    "deposit_amount, expected_balance",
    [(500.0, 1500.0), (0.01, 1000.01), (10000.0, 11000.0)],
)
def test_deposit_positive_amount(account_with_balance, deposit_amount, expected_balance):
    """Пополнение: допустимые суммы."""
    account_with_balance.deposit(deposit_amount)
    assert account_with_balance.balance == pytest.approx(expected_balance)


@pytest.mark.regression
@pytest.mark.parametrize("invalid_amount", [0.0, -50.0, -0.01])
def test_deposit_invalid_amount_raises_error(account_with_balance, invalid_amount):
    """Пополнение: нулевая или отрицательная сумма (ошибка)."""
    with pytest.raises(InvalidAmountError, match="Сумма должна быть > 0"):
        account_with_balance.deposit(invalid_amount)
    assert account_with_balance.balance == 1000.0  # баланс не изменился


# =====================================================================
# БЛОК 3: Снятие со счета (3 обязательных теста + параметризация)
# =====================================================================


@pytest.mark.smoke
@pytest.mark.parametrize(
    "withdraw_amount, expected_balance",
    [(100.0, 900.0), (1000.0, 0.0), (500.5, 499.5)],
)
def test_withdraw_valid_amount(account_with_balance, withdraw_amount, expected_balance):
    """Снятие: допустимые суммы (включая снятие всего остатка)."""
    account_with_balance.withdraw(withdraw_amount)
    assert account_with_balance.balance == pytest.approx(expected_balance)


@pytest.mark.regression
@pytest.mark.parametrize("overdraft_amount", [1000.01, 1500.0, 5000.0])
def test_withdraw_over_balance_raises_error(account_with_balance, overdraft_amount):
    """Снятие: превышение баланса (ошибка)."""
    with pytest.raises(InsufficientFundsError, match="Нельзя выдать"):
        account_with_balance.withdraw(overdraft_amount)
    assert account_with_balance.balance == 1000.0


@pytest.mark.regression
@pytest.mark.parametrize("invalid_withdraw", [0.0, -100.0])
def test_withdraw_negative_or_zero_amount_raises_error(
    account_with_balance, invalid_withdraw
):
    """Снятие: нулевая или отрицательная сумма (ошибка)."""
    with pytest.raises(InvalidAmountError):
        account_with_balance.withdraw(invalid_withdraw)


@pytest.mark.regression
def test_withdraw_from_empty_account_raises_error(empty_account):
    """Снятие с пустого счета запрещено."""
    with pytest.raises(InsufficientFundsError):
        empty_account.withdraw(0.01)


# =====================================================================
# БЛОК 4: Геттеры и строковые представления
# =====================================================================


def test_account_get_owner(account_with_balance):
    assert account_with_balance.owner == "Test"


@pytest.mark.smoke
def test_account_string_representation(account_with_balance):
    text = str(account_with_balance)
    assert "Test" in text
    assert "1000.00" in text


def test_account_repr(account_with_balance):
    assert repr(account_with_balance) == (
        "BankAccount(owner='Test', initial_balance=1000.0)"
    )


# =====================================================================
# БЛОК 5 (бонус): последовательность операций и иерархия исключений
# =====================================================================


def test_sequence_deposit_withdraw_deposit(account_with_balance):
    """Пополнить -> снять -> пополнить: проверяем итоговый баланс."""
    account_with_balance.deposit(500.0)
    account_with_balance.withdraw(300.0)
    account_with_balance.deposit(100.0)
    assert account_with_balance.balance == 1300.0


@pytest.mark.regression
@pytest.mark.parametrize(
    "exception_class",
    [NegativeInitialBalanceError, InvalidAmountError, InsufficientFundsError],
)
def test_custom_exceptions_inherit_base_error(exception_class):
    """Все собственные исключения ловятся через базовый BankAccountError."""
    assert issubclass(exception_class, BankAccountError)
