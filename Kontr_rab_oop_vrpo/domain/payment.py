from .transaction import Transaction


class PaymentTransaction(Transaction):
    def apply(self, account):
        account.available_credit += self.amount

        if self.amount >= account.debt:
            account.debt = 0
        else:
            account.debt -= self.amount
