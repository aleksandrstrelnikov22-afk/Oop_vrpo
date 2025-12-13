from .transaction import Transaction


class BonusTransaction(Transaction):
    def apply(self, account):
        account.bonuses += self.amount
