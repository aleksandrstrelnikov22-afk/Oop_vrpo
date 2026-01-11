from __future__ import annotations
from datetime import datetime

from domain.purchase import PurchaseTransaction
from domain.payment import PaymentTransaction
from domain.penalty import PenaltyTransaction
from domain.bonus import BonusTransaction


class TransactionFactory:
    @staticmethod
    def create(tr_type: str, *, amount: float, date: datetime, category: str, description: str, discount_percent: float | None = None):
        tr_type = tr_type.strip()

        if tr_type in ("PurchaseTransaction", "purchase", "Purchase"):
            return PurchaseTransaction(
                amount=amount,
                date=date,
                category=category,
                description=description,
                discount_percent=float(discount_percent or 0.0),
            )

        if tr_type in ("PaymentTransaction", "payment", "Payment"):
            return PaymentTransaction(amount=amount, date=date, category=category, description=description)

        if tr_type in ("PenaltyTransaction", "penalty", "Penalty"):
            return PenaltyTransaction(amount=amount, date=date, category=category, description=description)

        if tr_type in ("BonusTransaction", "bonus", "Bonus"):
            return BonusTransaction(amount=amount, date=date, category=category, description=description)

        raise ValueError(f"Unknown transaction type: {tr_type}")

    @staticmethod
    def to_row(tr) -> dict:

        tr_type = tr.__class__.__name__
        row = {
            "type": tr_type,
            "date": tr.date.isoformat(timespec="seconds"),
            "amount": float(tr.amount),
            "category": getattr(tr, "category", ""),
            "description": getattr(tr, "description", ""),
            "discount_percent": "",
        }
        if tr_type == "PurchaseTransaction":
            row["discount_percent"] = str(getattr(tr, "discount_percent", 0.0))
        return row

    @staticmethod
    def parse_date(s: str) -> datetime:
        # ISO (2024-01-01T12:00:00)
        return datetime.fromisoformat(s)
