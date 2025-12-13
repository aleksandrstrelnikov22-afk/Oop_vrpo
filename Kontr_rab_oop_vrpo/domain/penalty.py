from .transaction import Transaction


class PenaltyTransaction(Transaction):
    def apply(self, account):
        account.penalties += self.amount
        account.debt += self.amount
