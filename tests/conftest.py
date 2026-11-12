import pytest

from src.bank_account.account import BankAccount


@pytest.fixture
def account_with_balance() -> BankAccount:
    return BankAccount(owner="Test", initial_balance=1000.0)


@pytest.fixture
def empty_account() -> BankAccount:
    return BankAccount(owner="Empty", initial_balance=0.0)
