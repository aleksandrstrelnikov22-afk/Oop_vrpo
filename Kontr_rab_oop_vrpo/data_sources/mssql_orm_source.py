from __future__ import annotations

from sqlalchemy import (
    create_engine, Column, Integer, Float, String, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker

from data_sources.i_datasource import IDataSource
from data_sources.transaction_factory import TransactionFactory
from domain.credit_account import CreditAccount

Base = declarative_base()


class AccountRow(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True)  # всегда 1
    base_credit_limit = Column(Float, nullable=False)
    cashback_percent = Column(Float, nullable=False)
    last_bonus_payout_year = Column(Integer, nullable=True)
    last_bonus_payout_month = Column(Integer, nullable=True)


class TransactionRow(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(64), nullable=False)
    date = Column(String(32), nullable=False)  # ISO string
    amount = Column(Float, nullable=False)
    category = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)
    discount_percent = Column(Float, nullable=True)


class SqlAlchemyMSSQLDataSource(IDataSource):
    def __init__(self, sqlalchemy_url: str):
        # fast_executemany может ускорить массовые вставки, но необязательно
        self.engine = create_engine(sqlalchemy_url, future=True)
        self.Session = sessionmaker(bind=self.engine, future=True)

        # создаёт таблицы при первом запуске
        Base.metadata.create_all(self.engine)

        # гарантируем наличие записи account id=1
        with self.Session() as s:
            acc = s.get(AccountRow, 1)
            if acc is None:
                s.add(AccountRow(
                    id=1,
                    base_credit_limit=1000.0,
                    cashback_percent=0.01,
                    last_bonus_payout_year=None,
                    last_bonus_payout_month=None
                ))
                s.commit()

    def load_account(self) -> CreditAccount:
        with self.Session() as s:
            acc_row = s.get(AccountRow, 1)
            acc = CreditAccount(
                credit_limit_base=float(acc_row.base_credit_limit),
                cashback_percent=float(acc_row.cashback_percent),
            )
            if acc_row.last_bonus_payout_year is not None and acc_row.last_bonus_payout_month is not None:
                acc.last_bonus_payout_ym = (int(acc_row.last_bonus_payout_year), int(acc_row.last_bonus_payout_month))

            # загрузка операций
            rows = s.query(TransactionRow).order_by(TransactionRow.id.asc()).all()
            for r in rows:
                tr = TransactionFactory.create(
                    r.type,
                    amount=float(r.amount),
                    date=TransactionFactory.parse_date(r.date),
                    category=r.category or "",
                    description=r.description or "",
                    discount_percent=float(r.discount_percent or 0.0),
                )
                acc.add_transaction(tr)

            return acc

    def save_account(self, acc: CreditAccount) -> None:
        with self.Session() as s:
            # account
            acc_row = s.get(AccountRow, 1)
            y = None
            m = None
            if acc.last_bonus_payout_ym:
                y, m = acc.last_bonus_payout_ym

            acc_row.base_credit_limit = float(acc.base_credit_limit)
            acc_row.cashback_percent = float(acc.cashback_percent)
            acc_row.last_bonus_payout_year = y
            acc_row.last_bonus_payout_month = m

            # простой учебный вариант: перезапись истории
            s.query(TransactionRow).delete()

            for tr in acc.history:
                row = TransactionFactory.to_row(tr)
                disc = row["discount_percent"]
                s.add(TransactionRow(
                    type=row["type"],
                    date=row["date"],
                    amount=float(row["amount"]),
                    category=row["category"] or None,
                    description=row["description"] or None,
                    discount_percent=float(disc) if disc != "" else None
                ))

            s.commit()
