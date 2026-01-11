from .transaction import Transaction


class PurchaseTransaction(Transaction):
    def __init__(self, amount, date, category, description, discount_percent: float = 0.0):
        super().__init__(amount, date, category, description)
        self.discount_percent = discount_percent

    def _final_amount(self) -> float:
        # скидка в диапазоне 0..1
        d = self.discount_percent
        if d < 0:
            d = 0.0
        if d > 1:
            d = 1.0
        return self.amount * (1 - d)

    def is_valid(self, account):
        return account.available_credit >= self._final_amount()

    def apply(self, account):
        final_amount = self._final_amount()

        account.available_credit -= final_amount

        if account.available_credit < account.base_credit_limit:
            account.debt = account.base_credit_limit - account.available_credit
        else:
            account.debt = 0.0

        cashback = final_amount * account.cashback_percent
        account.bonuses += round(cashback, 2)
