import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from domain.credit_account import CreditAccount
from domain.purchase import PurchaseTransaction
from domain.payment import PaymentTransaction
from domain.penalty import PenaltyTransaction
from domain.bonus import BonusTransaction

from services.billing_service import BillingService

from data_sources.ds_factory import DataSourceFactory


DATE_FMT = "%Y-%m-%d"


class CreditCardGUI(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.master = master
        self.master.title("Credit Card Simulator")
        self.master.minsize(820, 520)
        self.var_purchase_discount = tk.StringVar()

        self.var_ds_kind = tk.StringVar(value="const")
        self.var_ds_path = tk.StringVar(value="data")  # для CSV
        self.var_db_path = tk.StringVar(value="data/credit.db")  # для SQLite
        self.var_mssql_url = tk.StringVar(
            value="mssql+pyodbc://@localhost/CreditCardDB?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
        )
        # MODEL
        self.default_limit = 1000.0
        self.default_cashback = 0.01
        self.default_penalty_percent = 0.05

        self.account = CreditAccount(self.default_limit, cashback_percent=self.default_cashback)
        self.billing_service = BillingService(penalty_percent=self.default_penalty_percent)

        # UI STATE
        self.var_base_limit = tk.StringVar()
        self.var_available = tk.StringVar()
        self.var_debt = tk.StringVar()
        self.var_bonuses = tk.StringVar()
        self.var_penalties = tk.StringVar()
        self.var_ops = tk.StringVar()
        self.var_cashback = tk.StringVar(value=str(self.default_cashback))
        self.var_penalty_percent = tk.StringVar(value=str(self.default_penalty_percent))
        self.var_current_date = tk.StringVar(value=datetime.now().strftime(DATE_FMT))

        self._build_ui()
        self.refresh()

    # UI BUILD

    def _build_ui(self):
        self.pack(fill="both", expand=True, padx=12, pady=12)

        style = ttk.Style(self.master)
        # стиль
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Верхняя сетка
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 10))

        left = ttk.LabelFrame(top, text="Состояние счёта")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right = ttk.LabelFrame(top, text="Регламент и параметры")
        right.pack(side="right", fill="y")

        # Состояние
        grid = ttk.Frame(left)
        grid.pack(fill="x", padx=10, pady=10)

        rows = [
            ("Базовый лимит:", self.var_base_limit),
            ("Доступный лимит:", self.var_available),
            ("Долг:", self.var_debt),
            ("Бонусы:", self.var_bonuses),
            ("Штрафы:", self.var_penalties),
            ("Операций:", self.var_ops),
        ]
        for r, (label, var) in enumerate(rows):
            ttk.Label(grid, text=label).grid(row=r, column=0, sticky="w", pady=2)
            ttk.Label(grid, textvariable=var, font=("Segoe UI", 10, "bold")).grid(row=r, column=1, sticky="w", pady=2)

        # Регламент
        reg = ttk.Frame(right)
        reg.pack(fill="x", padx=10, pady=10)

        ttk.Label(reg, text="Текущая дата (YYYY-MM-DD):").grid(row=0, column=0, sticky="w")
        ttk.Entry(reg, textvariable=self.var_current_date, width=18).grid(row=1, column=0, sticky="w", pady=(2, 8))

        ttk.Button(reg, text="Рассчитать (штрафы + перенос бонусов)", command=self.on_process_billing)\
            .grid(row=2, column=0, sticky="we", pady=(0, 10))

        ttk.Separator(reg).grid(row=9, column=0, sticky="we", pady=10)

        ttk.Label(reg, text="Источник данных:").grid(row=10, column=0, sticky="w")
        ds_combo = ttk.Combobox(reg, textvariable=self.var_ds_kind, values=["const", "csv", "sqlite", "mssql_orm"], state="readonly",
                                width=16)
        ds_combo.grid(row=11, column=0, sticky="w", pady=(2, 8))

        ttk.Label(reg, text="CSV папка (для csv):").grid(row=12, column=0, sticky="w")
        ttk.Entry(reg, textvariable=self.var_ds_path, width=20).grid(row=13, column=0, sticky="w", pady=(2, 8))

        ttk.Label(reg, text="SQLite файл (для sqlite):").grid(row=14, column=0, sticky="w")
        ttk.Entry(reg, textvariable=self.var_db_path, width=20).grid(row=15, column=0, sticky="w", pady=(2, 8))

        ttk.Label(reg, text="MSSQL URL (для mssql_orm):").grid(row=16, column=0, sticky="w")
        ttk.Entry(reg, textvariable=self.var_mssql_url, width=20).grid(row=17, column=0, sticky="w", pady=(2, 8))

        ttk.Button(reg, text="Загрузить", command=self.on_load).grid(row=18, column=0, sticky="we")
        ttk.Button(reg, text="Сохранить", command=self.on_save).grid(row=19, column=0, sticky="we", pady=(6, 0))

        # Параметры
        ttk.Label(reg, text="Кэшбэк % (например 0.01):").grid(row=3, column=0, sticky="w")
        ttk.Entry(reg, textvariable=self.var_cashback, width=18).grid(row=4, column=0, sticky="w", pady=(2, 8))

        ttk.Label(reg, text="Штраф % в месяц (например 0.05):").grid(row=5, column=0, sticky="w")
        ttk.Entry(reg, textvariable=self.var_penalty_percent, width=18).grid(row=6, column=0, sticky="w", pady=(2, 8))

        ttk.Button(reg, text="Применить параметры", command=self.on_apply_params).grid(row=7, column=0, sticky="we")
        ttk.Button(reg, text="Новая карта / Сброс", command=self.on_reset).grid(row=8, column=0, sticky="we", pady=(8, 0))

        # Центр
        mid = ttk.Frame(self)
        mid.pack(fill="x", pady=(0, 10))

        # Левый блок
        actions = ttk.LabelFrame(mid, text="Операции")
        actions.pack(side="left", fill="both", expand=True)

        act = ttk.Frame(actions)
        act.pack(fill="x", padx=10, pady=10)

        # Поля
        self.var_purchase_amount = tk.StringVar()
        self.var_payment_amount = tk.StringVar()
        self.var_manual_penalty = tk.StringVar()
        self.var_manual_bonus = tk.StringVar()

        # Покупка
        ttk.Label(act, text="Покупка (сумма):").grid(row=0, column=0, sticky="w")
        ttk.Entry(act, textvariable=self.var_purchase_amount, width=18).grid(row=0, column=1, sticky="w", padx=(8, 12))

        ttk.Label(act, text="Скидка (0..1):").grid(row=0, column=2, sticky="w")
        ttk.Entry(act, textvariable=self.var_purchase_discount, width=10).grid(row=0, column=3, sticky="w", padx=(8, 12))

        ttk.Button(act, text="Добавить покупку", command=self.on_add_purchase).grid(row=0, column=4, sticky="we")

        # Платёж
        ttk.Label(act, text="Платёж (сумма):").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(act, textvariable=self.var_payment_amount, width=18).grid(row=1, column=1, sticky="w", padx=(8, 12), pady=(8, 0))
        ttk.Button(act, text="Внести платёж", command=self.on_add_payment).grid(row=1, column=2, sticky="we", pady=(8, 0))

        # Штраф вручную
        ttk.Label(act, text="Штраф вручную (сумма):").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(act, textvariable=self.var_manual_penalty, width=18).grid(row=2, column=1, sticky="w", padx=(8, 12), pady=(8, 0))
        ttk.Button(act, text="Добавить штраф", command=self.on_add_penalty).grid(row=2, column=2, sticky="we", pady=(8, 0))

        # Бонус вручную ?
        ttk.Label(act, text="Бонус вручную (сумма):").grid(row=3, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(act, textvariable=self.var_manual_bonus, width=18).grid(row=3, column=1, sticky="w", padx=(8, 12), pady=(8, 0))
        ttk.Button(act, text="Добавить бонус", command=self.on_add_bonus).grid(row=3, column=2, sticky="we", pady=(8, 0))

        act.columnconfigure(2, weight=1)

        # Нижняя часть
        history = ttk.LabelFrame(self, text="История операций")
        history.pack(fill="both", expand=True)

        columns = ("date", "type", "amount", "category", "desc")
        self.tree = ttk.Treeview(history, columns=columns, show="headings", height=10)
        self.tree.heading("date", text="Дата")
        self.tree.heading("type", text="Тип")
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("category", text="Категория")
        self.tree.heading("desc", text="Описание")

        self.tree.column("date", width=110, anchor="w")
        self.tree.column("type", width=130, anchor="w")
        self.tree.column("amount", width=90, anchor="e")
        self.tree.column("category", width=140, anchor="w")
        self.tree.column("desc", width=320, anchor="w")

        scroll = ttk.Scrollbar(history, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scroll.pack(side="right", fill="y", padx=(0, 10), pady=10)

    # HELPERS

    def refresh(self):
        # Штрафы
        shown_penalties = 0.0 if self.account.debt == 0 else self.account.penalties

        self.var_base_limit.set(f"{self.account.base_credit_limit:.2f}")
        self.var_available.set(f"{self.account.available_credit:.2f}")
        self.var_debt.set(f"{self.account.debt:.2f}")
        self.var_bonuses.set(f"{self.account.bonuses:.2f}")
        self.var_penalties.set(f"{shown_penalties:.2f}")
        self.var_ops.set(str(len(self.account.history)))

        # Обновление таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)

        for tr in self.account.history[-200:]:  # чтобы не тормозило на огромной истории
            tr_type = tr.__class__.__name__
            dt = tr.date.strftime(DATE_FMT) if hasattr(tr, "date") else ""
            amount = getattr(tr, "amount", 0.0)
            category = getattr(tr, "category", "")
            desc = getattr(tr, "description", "")
            self.tree.insert("", "end", values=(dt, tr_type, f"{amount:.2f}", category, desc))

    def _parse_float(self, s: str, field_name: str) -> float:
        s = (s or "").strip()
        if not s:
            raise ValueError(f"Поле '{field_name}' пустое")
        val = float(s)
        if val < 0:
            raise ValueError(f"Поле '{field_name}' не может быть отрицательным")
        return val

    def _parse_date(self, s: str) -> datetime:
        s = (s or "").strip()
        return datetime.strptime(s, DATE_FMT)

    def _err(self, e: Exception):
        messagebox.showerror("Ошибка", str(e))

    # ACTIONS

    def on_apply_params(self):
        try:
            cb = float(self.var_cashback.get().strip())
            pp = float(self.var_penalty_percent.get().strip())
            if cb < 0 or pp < 0:
                raise ValueError("Проценты не могут быть отрицательными")

            self.account.cashback_percent = cb
            self.billing_service.penalty_percent = pp
            self.refresh()
        except Exception as e:
            self._err(e)

    def on_reset(self):
        try:
            self.account = CreditAccount(self.default_limit, cashback_percent=float(self.var_cashback.get().strip() or self.default_cashback))
            self.billing_service = BillingService(penalty_percent=float(self.var_penalty_percent.get().strip() or self.default_penalty_percent))
            self.refresh()
        except Exception as e:
            self._err(e)

    def on_process_billing(self):
        try:
            current_date = self._parse_date(self.var_current_date.get())
            self.billing_service.process(self.account, current_date)
            self.refresh()
        except Exception as e:
            self._err(e)

    def on_add_purchase(self):
        try:
            amount = self._parse_float(self.var_purchase_amount.get(), "Сумма покупки")

            disc_str = (self.var_purchase_discount.get() or "").strip()
            discount = float(disc_str) if disc_str else 0.0
            if discount < 0 or discount > 1:
                raise ValueError("Скидка должна быть в диапазоне 0..1")

            tr = PurchaseTransaction(
                amount=amount,
                date=datetime.now(),
                category="Purchase",
                description="GUI purchase",
                discount_percent=discount
            )
            self.account.add_transaction(tr)
            self.refresh()
        except Exception as e:
            self._err(e)

    def on_add_payment(self):
        try:
            amount = self._parse_float(self.var_payment_amount.get(), "Сумма платежа")
            tr = PaymentTransaction(
                amount=amount,
                date=datetime.now(),
                category="Payment",
                description="GUI payment"
            )
            self.account.add_transaction(tr)
            self.refresh()
        except Exception as e:
            self._err(e)

    def on_add_penalty(self):
        try:
            amount = self._parse_float(self.var_manual_penalty.get(), "Сумма штрафа")
            tr = PenaltyTransaction(
                amount=amount,
                date=datetime.now(),
                category="Penalty",
                description="Manual penalty"
            )
            self.account.add_transaction(tr)
            self.refresh()
        except Exception as e:
            self._err(e)

    def on_add_bonus(self):
        try:
            amount = self._parse_float(self.var_manual_bonus.get(), "Сумма бонуса")
            tr = BonusTransaction(
                amount=amount,
                date=datetime.now(),
                category="Bonus",
                description="Manual bonus"
            )
            self.account.add_transaction(tr)
            self.refresh()
        except Exception as e:
            self._err(e)

    def _current_ds(self):
        kind = self.var_ds_kind.get()
        if kind == "csv":
            return DataSourceFactory.create("csv", self.var_ds_path.get())
        if kind == "sqlite":
            return DataSourceFactory.create("sqlite", self.var_db_path.get())
        if kind == "mssql_orm":
            return DataSourceFactory.create("mssql_orm", self.var_mssql_url.get())
        return DataSourceFactory.create("const", "")

    def on_load(self):
        try:
            ds = self._current_ds()
            self.account = ds.load_account()
            # billing_service использует penalty_percent; можно оставить текущий или тоже хранить в источнике
            self.refresh()
        except Exception as e:
            self._err(e)

    def on_save(self):
        try:
            ds = self._current_ds()
            ds.save_account(self.account)
        except Exception as e:
            self._err(e)


def main():
    root = tk.Tk()
    app = CreditCardGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
