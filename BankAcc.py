class BankAccount:
    bank_name = "Центральный Банк"

    def __init__(self, owner: str, initial_balance: float = 0.0):
        self.owner = owner
        self._balance = 0.0
        self._transactions = []

        if initial_balance > 0:
            self.deposit(initial_balance)
            # Очищаем историю от стартового пополнения, чтобы красивее выводить отчет
            self._transactions.clear()

            # Устанавливаем стартовый баланс в чистом виде
        self._balance = initial_balance

    def _add_transaction(self, operation_type: str, amount: float):
        """Внутренний приватный метод для записи в историю."""
        self._transactions.append({
            "type": operation_type,
            "amount": amount,
            "balance_after": self._balance
        })

    def deposit(self, amount: float):
        """Пополнение счета с валидацией суммы."""
        if amount <= 0:
            print("ОШИБКА: Сумма пополнения должна быть положительной")
            return  # Метод завершается, программа НЕ падает

        self._balance += amount
        self._add_transaction("Пополнение", amount)

    def withdraw(self, amount: float):
        """Снятие средств с проверкой доступного остатка."""
        if amount <= 0:
            print("ОШИБКА: Сумма снятия должна быть положительной")
            return

        if amount > self._balance:
            print(f"ОШИБКА: Недостаточно средств для снятия {amount} руб. (доступно: {self._balance})")
            return  # Просто выводим ошибку, sys.exit() НЕ вызываем

        self._balance -= amount
        self._add_transaction("Снятие", amount)

    def get_balance(self) -> float:
        """Геттер для чтения баланса."""
        return self._balance

    def get_transactions(self) -> list:
        """Геттер возвращает копию истории, чтобы её нельзя было изменить извне."""
        return self._transactions.copy()
