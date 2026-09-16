from BankAcc import BankAccount

if __name__ == "__main__":
    account = BankAccount("Иван Петров", 1000.0)

    account.deposit(500)
    account.withdraw(200)
    account.withdraw(1500)
    account.deposit(-50)

    print("\n--- ДЕМОНСТРАЦИЯ РЕЗУЛЬТАТОВ ---")
    print(f"Владелец: {account.owner}")
    print(f"Баланс: {account.get_balance()}")

    print("История операций:")
    for tx in account.get_transactions():
        if tx['type'] == "Пополнение":
            print(f"  Пополнение: +{tx['amount']} руб. (баланс: {tx['balance_after']})")
        elif tx['type'] == "Снятие":
            print(f"  Снятие: -{tx['amount']} руб. (баланс: {tx['balance_after']})")
