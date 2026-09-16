balance = 0.0
history = []


def deposit(amount):
    global balance
    # Ошибка проектирования: скрипт вообще не проверяет, что сумма положительная
    balance += amount
    history.append(f"Пополнение: +{amount} руб.")


def withdraw(amount):
    global balance
    # Ошибка проектирования: при нехватке денег скрипт полностью падает
    if amount > balance:
        print(f"Попытка снять {amount} руб...")
        print("ОШИБКА! Недостаточно средств. Программа завершена.")

    balance -= amount
    history.append(f"Снятие: -{amount} руб.")


# Линейный запуск операций из задания
if __name__ == "__main__":
    print("Скрипт запущен...")

    # 1. Устанавливаем стартовый баланс (имитируем 1000 руб, как в системе)
    deposit(1000.0)

    # 2. Выполняем успешные операции
    deposit(500.0)
    print("Внесено 500 руб.")

    withdraw(200.0)
    print("Снято 200 руб.")


    withdraw(1500.0)
