from __future__ import annotations
import csv
import os
from datetime import datetime

from data_sources.i_datasource import IDataSource
from data_sources.transaction_factory import TransactionFactory
from domain.credit_account import CreditAccount


class CSVDataSource(IDataSource):
    def __init__(self, folder: str):
        self.folder = folder
        self.account_path = os.path.join(folder, "account.csv")
        self.tr_path = os.path.join(folder, "transactions.csv")

    def load_account(self) -> CreditAccount:
        os.makedirs(self.folder, exist_ok=True)

        base_limit = 1000.0
        cashback = 0.01
        last_y = ""
        last_m = ""

        if os.path.exists(self.account_path):
            with open(self.account_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
                    r = rows[0]
                    base_limit = float(r.get("base_credit_limit", base_limit))
                    cashback = float(r.get("cashback_percent", cashback))
                    last_y = r.get("last_bonus_payout_year", "")
                    last_m = r.get("last_bonus_payout_month", "")

        acc = CreditAccount(credit_limit_base=base_limit, cashback_percent=cashback)
        if last_y and last_m:
            acc.last_bonus_payout_ym = (int(last_y), int(last_m))

        # транзакции проигрываем (replay) — это восстанавливает состояние корректно
        if os.path.exists(self.tr_path):
            with open(self.tr_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    tr_type = row["type"]
                    date = TransactionFactory.parse_date(row["date"])
                    amount = float(row["amount"])
                    category = row.get("category", "")
                    desc = row.get("description", "")
                    disc = row.get("discount_percent", "")
                    disc_val = float(disc) if disc != "" else 0.0

                    tr = TransactionFactory.create(
                        tr_type,
                        amount=amount,
                        date=date,
                        category=category,
                        description=desc,
                        discount_percent=disc_val,
                    )
                    acc.add_transaction(tr)

        return acc

    def save_account(self, acc: CreditAccount) -> None:
        os.makedirs(self.folder, exist_ok=True)

        # сохраняем параметры аккаунта
        with open(self.account_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["base_credit_limit", "cashback_percent", "last_bonus_payout_year", "last_bonus_payout_month"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            y, m = ("", "")
            if acc.last_bonus_payout_ym:
                y, m = acc.last_bonus_payout_ym

            writer.writerow({
                "base_credit_limit": acc.base_credit_limit,
                "cashback_percent": acc.cashback_percent,
                "last_bonus_payout_year": y,
                "last_bonus_payout_month": m,
            })

        # сохраняем историю транзакций
        with open(self.tr_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["type", "date", "amount", "category", "description", "discount_percent"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for tr in acc.history:
                writer.writerow(TransactionFactory.to_row(tr))
