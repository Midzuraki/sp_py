import sys
from src.bank_account.storage import JsonStorage
from src.bank_account.account import BankAccount
from src.bank_account.exceptions import BankAccountError


def get_positive_float(prompt_text: str) -> float:
    while True:
        try:
            user_input = input(prompt_text).strip()
            if not user_input:
                print("Ошибка: поле не может быть пустым. Попробуйте снова.")
                continue
            amount = float(user_input)
            if amount <= 0:
                print("Ошибка: сумма должна быть строго больше нуля! Попробуйте снова.")
                continue
            return amount
        except ValueError:
            print("Ошибка: введите корректное число (например, 500 или 150.50).")


def main() -> None:
    storage = JsonStorage("accounts_db.json")
    print("\n=== ДОБРО ПОЖАЛОВАТЬ В СИСТЕМУ ЦЕНТРАЛЬНОГО БАНКА КИРИЕШЕК ===")

    owner = input("Введите имя владельца счета: ").strip()
    if not owner:
        print("Имя не может быть пустым. Выход.")
        return

    account = storage.load_account(owner)
    if account:
        print(f"Аккаунт найден! {account}")
    else:
        print(f"Аккаунт для '{owner}' не найден. Создаем новый...")
        while True:
            try:
                init_input = input("Введите начальный баланс (или 0): ").strip()
                init_bal = float(init_input if init_input else 0)
                if init_bal < 0:
                    print("Ошибка: начальный баланс не может быть отрицательным.")
                    continue
                break
            except ValueError:
                print("Ошибка: введите число для начального баланса.")

        account = BankAccount(owner, init_bal)
        storage.save_account(account)

    while True:
        print("\nДоступные операции:")
        print("1. Проверить баланс")
        print("2. Пополнить счет")
        print("3. Снять средства")
        print("4. Выйти")

        choice = input("Выберите действие (1-4): ").strip()

        try:
            if choice == "1":
                print(f"\nТекущий баланс счета {account.owner}: {account.balance:.2f} руб.")

            elif choice == "2":
                amount = get_positive_float("Введите сумму для пополнения: ")
                account.deposit(amount)
                storage.save_account(account)
                print(f"Успешно внесено {amount:.2f} руб.")

            elif choice == "3":
                amount = get_positive_float("Введите сумму для снятия: ")
                account.withdraw(amount)
                storage.save_account(account)
                print(f"Успешно снято {amount:.2f} руб.")

            elif choice == "4":
                break
            else:
                print("Неверный пункт меню. Попробуйте еще раз.")

        except BankAccountError as e:
            print(f"Ошибка выполнения операции: {e}")


if __name__ == "__main__":
    main()
