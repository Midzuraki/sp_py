"""ЛР1, этап 4: демонстрация класса BankAccount. Программа НЕ падает при ошибках."""
from BankAcc import BankAccount

if __name__ == "__main__":
    account = BankAccount("Иван Петров", 1000.0)
    errors = []  # ошибки собираем и печатаем вместе с историей

    operations = [
        ("deposit", 500),
        ("withdraw", 200),
        ("withdraw", 1500),  # больше, чем есть на счёте
        ("deposit", -50),  # отрицательная сумма
    ]
    for name, amount in operations:
        try:
            getattr(account, name)(amount)
        except ValueError as exc:  # ошибка обработана, программа продолжает работу
            errors.append(str(exc))

    print(f"Владелец: {account.owner}")
    print(f"Баланс: {account.get_balance()}")
    print("История операций:")
    for tx in account.get_transactions():
        sign = "+" if tx["type"] == "Пополнение" else "-"
        print(
            f"  {tx['type']}: {sign}{tx['amount']:g} руб. "
            f"(баланс: {tx['balance_after']:g})"
        )
    for message in errors:
        print(f"  ОШИБКА: {message}")
