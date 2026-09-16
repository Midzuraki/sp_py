class BankAccountError(Exception):
    pass

class NegativeInitialBalanceError(BankAccountError):
    pass

class InvalidAmountError(BankAccountError):
    pass

class InsufficientFundsError(BankAccountError):
    pass
