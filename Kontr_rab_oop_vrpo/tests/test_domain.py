import unittest
from datetime import datetime

from domain.credit_account import CreditAccount
from domain.purchase import PurchaseTransaction
from domain.payment import PaymentTransaction
from domain.penalty import PenaltyTransaction

from services.billing_service import BillingService


class TestCreditAccountDomain(unittest.TestCase):

    def test_purchase_with_discount_and_cashback(self):
        """
        Покупка со скидкой уменьшает доступный лимит на сумму после скидки,
        корректно пересчитывает долг и начисляет кэшбэк (процент от суммы после скидки).
        """
        acc = CreditAccount(1000, cashback_percent=0.01)

        tr = PurchaseTransaction(
            amount=500,
            date=datetime(2024, 1, 10),
            category="Purchase",
            description="Test purchase",
            discount_percent=0.10  # 10%
        )
        acc.add_transaction(tr)

        # final_amount = 500 * (1 - 0.1) = 450
        self.assertAlmostEqual(acc.available_credit, 550.0, places=2)
        self.assertAlmostEqual(acc.debt, 450.0, places=2)

        # cashback = 450 * 1% = 4.50
        self.assertAlmostEqual(acc.bonuses, 4.50, places=2)

    def test_payment_increases_available_and_reduces_debt(self):
        """
        Платёж увеличивает доступный лимит, долг пересчитывается из available_credit.
        """
        acc = CreditAccount(1000, cashback_percent=0.01)

        # Создаём долг покупкой на 600
        acc.add_transaction(PurchaseTransaction(
            amount=600,
            date=datetime(2024, 1, 1),
            category="Purchase",
            description="Make debt",
            discount_percent=0.0
        ))
        self.assertAlmostEqual(acc.debt, 600.0, places=2)
        self.assertAlmostEqual(acc.available_credit, 400.0, places=2)

        # Платёж 200
        acc.add_transaction(PaymentTransaction(
            amount=200,
            date=datetime(2024, 1, 2),
            category="Payment",
            description="Pay 200"
        ))

        # available: 400 + 200 = 600, debt = 1000 - 600 = 400
        self.assertAlmostEqual(acc.available_credit, 600.0, places=2)
        self.assertAlmostEqual(acc.debt, 400.0, places=2)

    def test_purchase_rejected_if_not_enough_available_credit(self):
        """
        Покупка должна отклоняться, если available_credit < сумма после скидки.
        """
        acc = CreditAccount(1000, cashback_percent=0.01)

        # Сначала забираем почти весь лимит
        acc.add_transaction(PurchaseTransaction(
            amount=990,
            date=datetime(2024, 1, 1),
            category="Purchase",
            description="Big purchase",
            discount_percent=0.0
        ))
        self.assertAlmostEqual(acc.available_credit, 10.0, places=2)

        # Пытаемся купить на 50 (не хватает)
        tr = PurchaseTransaction(
            amount=50,
            date=datetime(2024, 1, 2),
            category="Purchase",
            description="Should fail",
            discount_percent=0.0
        )

        with self.assertRaises(ValueError):
            acc.add_transaction(tr)

    def test_penalty_updates_penalties_and_affects_debt_via_available(self):
        """
        Штраф должен увеличивать penalties и уменьшать available_credit,
        а debt пересчитывается из available_credit.
        """
        acc = CreditAccount(1000, cashback_percent=0.01)

        # Создадим долг 300
        acc.add_transaction(PurchaseTransaction(
            amount=300,
            date=datetime(2024, 1, 1),
            category="Purchase",
            description="Make debt",
            discount_percent=0.0
        ))
        self.assertAlmostEqual(acc.debt, 300.0, places=2)
        self.assertAlmostEqual(acc.available_credit, 700.0, places=2)

        # Штраф 50
        acc.add_transaction(PenaltyTransaction(
            amount=50,
            date=datetime(2024, 1, 5),
            category="Penalty",
            description="Penalty"
        ))

        self.assertAlmostEqual(acc.penalties, 50.0, places=2)
        # available 700 - 50 = 650 -> debt = 350
        self.assertAlmostEqual(acc.available_credit, 650.0, places=2)
        self.assertAlmostEqual(acc.debt, 350.0, places=2)

    def test_discount_100_percent_makes_purchase_free_and_no_cashback(self):
        """
        При скидке 100% сумма списания = 0, долг не растёт, кэшбэк = 0.
        """
        acc = CreditAccount(1000, cashback_percent=0.01)

        acc.add_transaction(PurchaseTransaction(
            amount=500,
            date=datetime(2024, 1, 1),
            category="Purchase",
            description="Free purchase",
            discount_percent=1.0
        ))

        self.assertAlmostEqual(acc.available_credit, 1000.0, places=2)
        self.assertAlmostEqual(acc.debt, 0.0, places=2)
        self.assertAlmostEqual(acc.bonuses, 0.0, places=2)

    def test_discount_out_of_range_is_clamped(self):
        """
        Скидка меньше 0 трактуется как 0, больше 1 как 1 (если ты сделал clamp).
        """
        acc = CreditAccount(1000, cashback_percent=0.01)

        # discount < 0 => 0
        acc.add_transaction(PurchaseTransaction(
            amount=200,
            date=datetime(2024, 1, 1),
            category="Purchase",
            description="Neg discount",
            discount_percent=-5.0
        ))
        # final_amount = 200
        self.assertAlmostEqual(acc.available_credit, 800.0, places=2)

        # discount > 1 => 1
        acc.add_transaction(PurchaseTransaction(
            amount=300,
            date=datetime(2024, 1, 2),
            category="Purchase",
            description="Over discount",
            discount_percent=5.0
        ))
        # final_amount = 0
        self.assertAlmostEqual(acc.available_credit, 800.0, places=2)

    def test_payment_fully_closes_debt(self):
        """
        Платёж должен полностью закрыть долг, если его достаточно.
        """
        acc = CreditAccount(1000, cashback_percent=0.01)

        acc.add_transaction(PurchaseTransaction(
            amount=400,
            date=datetime(2024, 1, 1),
            category="Purchase",
            description="Make debt",
            discount_percent=0.0
        ))
        self.assertAlmostEqual(acc.debt, 400.0, places=2)

        acc.add_transaction(PaymentTransaction(
            amount=400,
            date=datetime(2024, 1, 2),
            category="Payment",
            description="Close debt"
        ))
        self.assertAlmostEqual(acc.debt, 0.0, places=2)
        self.assertAlmostEqual(acc.available_credit, 1000.0, places=2)

    def test_payment_overpays_makes_available_credit_above_base(self):
        """
        Переплата: available_credit может стать больше base_credit_limit, debt при этом 0.
        """
        acc = CreditAccount(1000, cashback_percent=0.01)

        # Создаём долг 600 (available=400)
        acc.add_transaction(PurchaseTransaction(
            amount=600,
            date=datetime(2024, 1, 1),
            category="Purchase",
            description="Make debt",
            discount_percent=0.0
        ))
        self.assertAlmostEqual(acc.available_credit, 400.0, places=2)

        # Платёж 1000 => available 1400, debt 0
        acc.add_transaction(PaymentTransaction(
            amount=1000,
            date=datetime(2024, 1, 2),
            category="Payment",
            description="Overpay"
        ))

        self.assertAlmostEqual(acc.debt, 0.0, places=2)
        self.assertAlmostEqual(acc.available_credit, 1400.0, places=2)




class TestBillingService(unittest.TestCase):

    def test_monthly_penalty_is_capped_at_50_percent_of_base_limit(self):
        """
        BillingService начисляет штраф(ы), но суммарные штрафы не превышают 50% базового лимита.
        """
        acc = CreditAccount(1000, cashback_percent=0.01)

        # Делаем долг 1000
        acc.add_transaction(PurchaseTransaction(
            amount=1000,
            date=datetime(2024, 1, 1),
            category="Purchase",
            description="Max out",
            discount_percent=0.0
        ))
        self.assertAlmostEqual(acc.debt, 1000.0, places=2)
        self.assertAlmostEqual(acc.available_credit, 0.0, places=2)

        billing = BillingService(penalty_percent=0.05)

        # Через 2 года (24 месяца) штраф без cap был бы огромный,
        # но cap = 50% * 1000 = 500
        billing.process(acc, datetime(2026, 1, 1))

        self.assertAlmostEqual(acc.penalties, 500.0, places=2)

        # Повторный вызов в том же месяце не должен увеличивать штрафы (months_between=0)
        prev_penalties = acc.penalties
        billing.process(acc, datetime(2026, 1, 15))
        self.assertAlmostEqual(acc.penalties, prev_penalties, places=2)

    def test_bonus_payout_happens_once_per_month(self):
        """
        Перенос бонусов на основной счёт происходит один раз при первом расчёте в новом месяце.
        """
        acc = CreditAccount(1000, cashback_percent=0.01)

        # Покупка 500 -> бонусы = 5.00
        acc.add_transaction(PurchaseTransaction(
            amount=500,
            date=datetime(2024, 1, 10),
            category="Purchase",
            description="For cashback",
            discount_percent=0.0
        ))
        self.assertAlmostEqual(acc.bonuses, 5.0, places=2)

        # Чтобы штрафы не мешали — ставим penalty_percent=0
        billing = BillingService(penalty_percent=0.0)

        # Первый расчёт в феврале -> должен перенести бонусы
        before_available = acc.available_credit
        billing.process(acc, datetime(2024, 2, 5))

        self.assertAlmostEqual(acc.bonuses, 0.0, places=2)
        self.assertTrue(acc.available_credit >= before_available)  # стал больше из-за "платежа бонусами"
        self.assertEqual(acc.last_bonus_payout_ym, (2024, 2))

        # Повторно в этом же месяце — перенос не должен повториться
        prev_available = acc.available_credit
        billing.process(acc, datetime(2024, 2, 20))
        self.assertAlmostEqual(acc.available_credit, prev_available, places=2)

    def test_penalties_not_applied_when_debt_zero(self):
        """
        Если debt == 0, то штрафы не начисляются даже при большой разнице дат.
        """
        acc = CreditAccount(1000, cashback_percent=0.01)
        billing = BillingService(penalty_percent=0.05)

        # Истории нет -> ничего
        billing.process(acc, datetime(2026, 1, 1))
        self.assertAlmostEqual(acc.penalties, 0.0, places=2)

        # Добавим платёж (чтобы появилась история), debt всё равно 0
        acc.add_transaction(PaymentTransaction(
            amount=100,
            date=datetime(2024, 1, 1),
            category="Payment",
            description="Just to create history"
        ))
        billing.process(acc, datetime(2026, 1, 1))
        self.assertAlmostEqual(acc.penalties, 0.0, places=2)

    def test_bonus_payout_marks_month_even_if_no_bonuses(self):
        """
        Если бонусов нет, сервис всё равно запоминает, что в этом месяце расчёт был,
        чтобы не пытаться снова (по твоей текущей логике).
        """
        acc = CreditAccount(1000, cashback_percent=0.01)
        acc.add_transaction(PurchaseTransaction(
            amount=50,  # cashback 0.50, но зависит от %; при 1% будет 0.5, не ноль
            date=datetime(2024, 1, 10),
            category="Purchase",
            description="Small purchase",
            discount_percent=0.0
        ))

        # Обнулим бонусы вручную, чтобы смоделировать "нет бонусов"
        acc.bonuses = 0.0

        billing = BillingService(penalty_percent=0.0)
        billing.process(acc, datetime(2024, 2, 3))

        self.assertEqual(acc.last_bonus_payout_ym, (2024, 2))
        self.assertAlmostEqual(acc.bonuses, 0.0, places=2)

    def test_bonus_payout_does_not_repeat_next_call_same_month(self):
        """
        Дважды в одном месяце payout не должен повторяться.
        """
        acc = CreditAccount(1000, cashback_percent=0.01)

        acc.add_transaction(PurchaseTransaction(
            amount=1000,  # бонусы 10 при 1%
            date=datetime(2024, 1, 10),
            category="Purchase",
            description="Cashback",
            discount_percent=0.0
        ))
        self.assertAlmostEqual(acc.bonuses, 10.0, places=2)

        billing = BillingService(penalty_percent=0.0)

        billing.process(acc, datetime(2024, 2, 1))
        after_first = acc.available_credit

        # Бонусы уже перенесены и last_bonus_payout_ym установлен
        billing.process(acc, datetime(2024, 2, 28))
        self.assertAlmostEqual(acc.available_credit, after_first, places=2)

    def test_months_between_basic(self):
        """
        Проверяем корректность расчёта месяцев.
        """
        b = BillingService(penalty_percent=0.0)
        self.assertEqual(b._months_between(datetime(2024, 1, 1), datetime(2024, 1, 31)), 0)
        self.assertEqual(b._months_between(datetime(2024, 1, 1), datetime(2024, 2, 1)), 1)
        self.assertEqual(b._months_between(datetime(2024, 1, 15), datetime(2024, 3, 1)), 2)
        self.assertEqual(b._months_between(datetime(2024, 12, 1), datetime(2025, 1, 1)), 1)



if __name__ == "__main__":
    unittest.main()
