class CreditAccount:
    def __init__(self, credit_limit_base: float, cashback_percent: float = 0.01):
        self.base_credit_limit = credit_limit_base
        self.available_credit = credit_limit_base
        self.debt = 0.0
        self.bonuses = 0.0
        self.penalties = 0.0
        self.history = []
        self.cashback_percent = cashback_percent
        self.last_bonus_payout_ym = None

    def can_apply(self, transaction) -> bool:
        return transaction.is_valid(self)

    def add_transaction(self, transaction):
        if not self.can_apply(transaction):
            raise ValueError("Операция недопустима")

        transaction.apply(self)
        self.history.append(transaction)

    def summary(self) -> dict:
        return {
            "base_credit_limit": self.base_credit_limit,
            "available_credit": self.available_credit,
            "debt": self.debt,
            "bonuses": self.bonuses,
            "penalties": self.penalties,
            "operations": len(self.history),
            "cashback_percent": self.cashback_percent,
        }
