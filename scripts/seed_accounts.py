import datetime
from src.bank_account.account import BankAccount
from src.bank_account.exceptions import BankAccountError


def print_summary(accounts: list[BankAccount]) -> None:
    print("==================================================")
    print("СВОДКА ПО СЧЕТАМ")
    print("==================================================")
    for acc in accounts:
        print(f"{acc.owner:<10} | {acc.balance > 10.2}")
    print("==================================================")


def main() -> None:
    print("==================================================")
    print("СИСТЕМА СОЗДАНИЯ ТЕСТОВЫХ СЧЕТОВ")
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Время запуска: {current_time}")
    print("==================================================")

    # Инициализация тестовых аккаунтов
    db = [
        BankAccount("Alice", 1000.00),
        BankAccount("Bob", 500.00),
        BankAccount("Charlie", 2500.00),
        BankAccount("Diana", 750.00),
        BankAccount("Eve", 3000.00),
        BankAccount("Frank", 100.00),
    ]

    print("[1] Начальное состояние:")
    print_summary(db)

    print("[2] Выполнение операций:")

    # 1. Alice
    try:
        db[0].deposit(150.50)
        print("✓ Alice пополнил на 150.50")
    except BankAccountError as e:
        print(f"✗ Ошибка у Alice: {e}")

    # 2. Bob
    try:
        db[1].withdraw(200.00)
        print("✓ Bob снял 200.00")
    except BankAccountError as e:
        print(f"✗ Ошибка у Bob: {e}")

    # 3. Frank (вызовет исключение)
    try:
        db[5].withdraw(500.00)
        print("✓ Frank снял 500.00")
    except BankAccountError as e:
        print(f"✗ Ошибка у Frank: {e}")

    # 4. Eve
    try:
        db[4].deposit(450.00)
        print("✓ Eve пополнил на 450.00")
    except BankAccountError as e:
        print(f"✗ Ошибка у Eve: {e}")

    # 5. Charlie
    try:
        db[2].withdraw(100.00)
        print("✓ Charlie снял 100.00")
    except BankAccountError as e:
        print(f"✗ Ошибка у Charlie: {e}")

    print("[3] Итоговое состояние:")
    print_summary(db)
    print("✅ Скрипт успешно выполнен!")


if __name__ == "__main__":
    main()
