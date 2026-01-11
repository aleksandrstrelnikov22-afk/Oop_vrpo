from .transaction import Transaction

class PaymentTransaction(Transaction):
    def apply(self, account):
        account.available_credit += self.amount

        if account.available_credit < account.base_credit_limit:
            account.debt = account.base_credit_limit - account.available_credit
        else:
            account.debt = 0.0
