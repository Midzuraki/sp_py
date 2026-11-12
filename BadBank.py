"""ЛР1, этап 0: скрипт-антипаттерн (писался без ИИ).

Намеренно плохой код: глобальные переменные, нет проверки суммы,
нет логирования, при ошибке программа падает через exit().
"""
import sys

balance = 0
history = []


def deposit(amount):
    global balance
    # Нет проверки, что сумма положительная (можно внести -500!)
    balance += amount
    history.append(f"Пополнение: +{amount} руб.")
    print(f"Внесено {amount} руб.")


def withdraw(amount):
    global balance
    if amount > balance:
        print(f"Попытка снять {amount} руб...")
        print("ОШИБКА! Недостаточно средств. Программа завершена.")
        sys.exit()  # при любой ошибке скрипт просто падает
    balance -= amount
    history.append(f"Снятие: -{amount} руб.")
    print(f"Снято {amount} руб.")


# Линейный запуск: 3-4 операции и завершение
print("Скрипт запущен...")
deposit(1000)
withdraw(200)
withdraw(900)
print("До этой строки программа не дойдёт")
