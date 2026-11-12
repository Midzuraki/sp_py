"""Демонстрация работы класса BankAccount из пакета src (запуск: python -m scripts.demo)."""
from src.bank_account.account import BankAccount
from src.bank_account.exceptions import BankAccountError


def main() -> None:
    account = BankAccount("Иван Петров", 1000.0)
    print(account)
    print(repr(account))

    operations = [
        ("пополнение +500", account.deposit, 500.0),
        ("снятие -200", account.withdraw, 200.0),
        ("снятие -1500 (слишком много)", account.withdraw, 1500.0),
        ("пополнение -50 (некорректно)", account.deposit, -50.0),
    ]
    for title, operation, amount in operations:
        try:
            operation(amount)
            print(f"✓ {title}: баланс {account.balance:.2f}")
        except BankAccountError as exc:  # один except на все ошибки счета
            print(f"✗ {title}: {exc}")

    print(f"Итоговый баланс: {account.balance:.2f} руб.")


if __name__ == "__main__":
    main()
