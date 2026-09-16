import pytest
from src.bank_account.account import BankAccount
from src.bank_account.exceptions import (
    NegativeInitialBalanceError,
    InvalidAmountError,
    InsufficientFundsError
)

# =====================================================================
# БЛОК 1: Создание счета (3 обязательных теста)
# =====================================================================

@pytest.mark.smoke
def test_create_account_positive_balance():
    """Позитивный баланс при создании"""
    account = BankAccount(owner="Ivan", initial_balance=500.0)
    assert account.balance == 500.0

def test_create_account_zero_balance():
    """Нулевой баланс при создании"""
    account = BankAccount(owner="Ivan", initial_balance=0.0)
    assert account.balance == 0.0

@pytest.mark.regression
def test_create_account_negative_balance_raises_error():
    """Отрицательный баланс при создании (ошибка)"""
    with pytest.raises(NegativeInitialBalanceError):
        BankAccount(owner="Ivan", initial_balance=-100.0)


# =====================================================================
# БЛОК 2: Пополнение счета (2 обязательных теста + Параметризация)
# =====================================================================

@pytest.mark.smoke
@pytest.mark.parametrize("deposit_amount, expected_balance", [
    (500.0, 1500.0),
    (0.01, 1000.01),
    (10000.0, 11000.0)
])
def test_deposit_positive_amount(account_with_balance, deposit_amount, expected_balance):
    """Пополнение: позитивная сумма с параметризацией различных значений"""
    account_with_balance.deposit(deposit_amount)
    assert account_with_balance.balance == expected_balance

@pytest.mark.regression
@pytest.mark.parametrize("invalid_amount", [0.0, -50.0, -0.01])
def test_deposit_invalid_amount_raises_error(account_with_balance, invalid_amount):
    """Пополнение: отрицательная или нулевая сумма (ошибка)"""
    with pytest.raises(InvalidAmountError):
        account_with_balance.deposit(invalid_amount)


# =====================================================================
# БЛОК 3: Снятие со счета (3 обязательных теста + Параметризация)
# =====================================================================

@pytest.mark.parametrize("withdraw_amount, expected_balance", [
    (100.0, 900.0),
    (1000.0, 0.0),
    (500.5, 499.5)
])
def test_withdraw_valid_amount(account_with_balance, withdraw_amount, expected_balance):
    """Снятие: допустимая сумма с параметризацией различных значений"""
    account_with_balance.withdraw(withdraw_amount)
    assert account_with_balance.balance == expected_balance

@pytest.mark.regression
@pytest.mark.parametrize("overdraft_amount", [1000.01, 1500.0, 5000.0])
def test_withdraw_over_balance_raises_error(account_with_balance, overdraft_amount):
    """Снятие: превышение баланса (ошибка)"""
    with pytest.raises(InsufficientFundsError):
        account_with_balance.withdraw(overdraft_amount)

@pytest.mark.regression
@pytest.mark.parametrize("invalid_withdraw", [0.0, -100.0])
def test_withdraw_negative_or_zero_amount_raises_error(account_with_balance, invalid_withdraw):
    """Снятие: отрицательная или нулевая сумма (ошибка)"""
    with pytest.raises(InvalidAmountError):
        account_with_balance.withdraw(invalid_withdraw)


# =====================================================================
# БЛОК 4: Геттеры и строки (2 обязательных теста)
# =====================================================================

def test_account_get_owner(account_with_balance):
    assert account_with_balance.owner == "Test"

@pytest.mark.smoke
def test_account_string_representation(account_with_balance):
    assert "Test" in str(account_with_balance)
    assert "1000.00" in str(account_with_balance)
