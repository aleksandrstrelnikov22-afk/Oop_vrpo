from .transaction import Transaction

class PenaltyTransaction(Transaction):
    def apply(self, account):
        account.penalties += self.amount

        # штраф
        account.available_credit -= self.amount

        # долг
        if account.available_credit < account.base_credit_limit:
            account.debt = account.base_credit_limit - account.available_credit
        else:
            account.debt = 0.0
