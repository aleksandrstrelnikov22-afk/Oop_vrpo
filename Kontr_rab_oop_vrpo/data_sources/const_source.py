from __future__ import annotations
from datetime import datetime

from data_sources.i_datasource import IDataSource
from domain.credit_account import CreditAccount
from domain.purchase import PurchaseTransaction
from domain.payment import PaymentTransaction


class ConstDataSource(IDataSource):
    def load_account(self) -> CreditAccount:
        acc = CreditAccount(credit_limit_base=1000, cashback_percent=0.01)

        acc.add_transaction(PurchaseTransaction(
            amount=500,
            date=datetime(2024, 1, 10, 12, 0, 0),
            category="Shop",
            description="Test purchase",
            discount_percent=0.10,
        ))

        acc.add_transaction(PaymentTransaction(
            amount=200,
            date=datetime(2024, 1, 15, 12, 0, 0),
            category="Payment",
            description="Test payment",
        ))

        return acc

    def save_account(self, acc: CreditAccount) -> None:
        # Константный источник — заглушка, сохранять некуда
        return
