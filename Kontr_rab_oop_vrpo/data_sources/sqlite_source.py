from __future__ import annotations
import sqlite3
from datetime import datetime

from data_sources.i_datasource import IDataSource
from data_sources.transaction_factory import TransactionFactory
from domain.credit_account import CreditAccount


class SQLiteDataSource(IDataSource):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as con:
            cur = con.cursor()

            cur.execute("""
            CREATE TABLE IF NOT EXISTS account (
              id INTEGER PRIMARY KEY CHECK (id = 1),
              base_credit_limit REAL NOT NULL,
              cashback_percent REAL NOT NULL,
              last_bonus_payout_year INTEGER,
              last_bonus_payout_month INTEGER
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              type TEXT NOT NULL,
              date TEXT NOT NULL,
              amount REAL NOT NULL,
              category TEXT,
              description TEXT,
              discount_percent REAL
            )
            """)

            # если аккаунт не создан — вставим дефолт
            cur.execute("SELECT COUNT(*) FROM account")
            if cur.fetchone()[0] == 0:
                cur.execute("""
                INSERT INTO account (id, base_credit_limit, cashback_percent, last_bonus_payout_year, last_bonus_payout_month)
                VALUES (1, 1000.0, 0.01, NULL, NULL)
                """)
            con.commit()

    def load_account(self) -> CreditAccount:
        with self._connect() as con:
            cur = con.cursor()

            cur.execute("SELECT base_credit_limit, cashback_percent, last_bonus_payout_year, last_bonus_payout_month FROM account WHERE id=1")
            base_limit, cashback, y, m = cur.fetchone()

            acc = CreditAccount(credit_limit_base=float(base_limit), cashback_percent=float(cashback))
            if y is not None and m is not None:
                acc.last_bonus_payout_ym = (int(y), int(m))

            cur.execute("SELECT type, date, amount, category, description, discount_percent FROM transactions ORDER BY id ASC")
            for tr_type, date_s, amount, category, desc, disc in cur.fetchall():
                date = TransactionFactory.parse_date(date_s)
                tr = TransactionFactory.create(
                    tr_type,
                    amount=float(amount),
                    date=date,
                    category=category or "",
                    description=desc or "",
                    discount_percent=float(disc or 0.0),
                )
                acc.add_transaction(tr)

            return acc

    def save_account(self, acc: CreditAccount) -> None:
        with self._connect() as con:
            cur = con.cursor()

            y = None
            m = None
            if acc.last_bonus_payout_ym:
                y, m = acc.last_bonus_payout_ym

            cur.execute("""
            UPDATE account
               SET base_credit_limit=?,
                   cashback_percent=?,
                   last_bonus_payout_year=?,
                   last_bonus_payout_month=?
             WHERE id=1
            """, (acc.base_credit_limit, acc.cashback_percent, y, m))

            # перезаписываем транзакции (для контрольной это нормально)
            cur.execute("DELETE FROM transactions")
            for tr in acc.history:
                row = TransactionFactory.to_row(tr)
                cur.execute("""
                INSERT INTO transactions(type, date, amount, category, description, discount_percent)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    row["type"],
                    row["date"],
                    row["amount"],
                    row["category"],
                    row["description"],
                    float(row["discount_percent"]) if row["discount_percent"] != "" else None
                ))

            con.commit()
