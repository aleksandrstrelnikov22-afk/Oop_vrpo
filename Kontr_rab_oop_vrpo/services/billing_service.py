from datetime import datetime
from domain.penalty import PenaltyTransaction
from domain.payment import PaymentTransaction


class BillingService:
    def __init__(self, penalty_percent: float):
        self.penalty_percent = penalty_percent

    def process(self, account, current_date: datetime):
        # ежемесячные штрафы
        self._process_monthly_penalties(account, current_date)

        # перенос бонусов на основной счёт
        self._process_monthly_bonus_payout(account, current_date)

    def _process_monthly_penalties(self, account, current_date: datetime):
        if not account.history:
            return
        if account.debt <= 0:
            return

        last_date = account.history[-1].date
        months_passed = self._months_between(last_date, current_date)
        if months_passed <= 0:
            return

        # максимальная сумма штрафов
        max_penalties = round(account.base_credit_limit * 0.5, 2)

        # если уже достигли капа
        if account.penalties >= max_penalties:
            return

        # штраф за период
        base_debt = account.debt
        penalty_total = round(base_debt * self.penalty_percent * months_passed, 2)


        remaining_cap = round(max_penalties - account.penalties, 2)
        penalty_total = min(penalty_total, remaining_cap)

        if penalty_total <= 0:
            return

        penalty = PenaltyTransaction(
            amount=penalty_total,
            date=current_date,
            category="Monthly penalty",
            description=f"Штраф {self.penalty_percent * 100:.1f}% за {months_passed} мес. (cap 50%)"
        )
        account.add_transaction(penalty)

    def _process_monthly_bonus_payout(self, account, current_date: datetime):
        current_ym = (current_date.year, current_date.month)

        if account.last_bonus_payout_ym == current_ym:
            return

        if account.bonuses <= 0:
            account.last_bonus_payout_ym = current_ym
            return

        payout_amount = round(account.bonuses, 2)


        payout = PaymentTransaction(
            amount=payout_amount,
            date=current_date,
            category="Bonus payout",
            description="Перенос бонусов на основной счёт"
        )
        account.add_transaction(payout)


        account.bonuses = 0.0
        account.last_bonus_payout_ym = current_ym

    @staticmethod
    def _months_between(d1: datetime, d2: datetime) -> int:
        return (d2.year - d1.year) * 12 + (d2.month - d1.month)
