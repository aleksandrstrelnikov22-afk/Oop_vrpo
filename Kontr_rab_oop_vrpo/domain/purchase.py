from .transaction import Transaction


class PurchaseTransaction(Transaction):
    def __init__(self, amount, date, category, description,
                 discount_percent=0.0, bonus_percent=0.0):
        super().__init__(amount, date, category, description)
        self.discount_percent = discount_percent
        self.bonus_percent = bonus_percent

    def is_valid(self, account):
        final_amount = self.amount * (1 - self.discount_percent)
        return account.available_credit >= final_amount

    def apply(self, account):
        final_amount = self.amount * (1 - self.discount_percent)

        account.available_credit -= final_amount

        if account.available_credit < account.base_credit_limit:
            account.debt = account.base_credit_limit - account.available_credit

        account.bonuses += final_amount * self.bonus_percent
