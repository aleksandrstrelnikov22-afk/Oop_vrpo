from datetime import datetime
from domain.credit_account import CreditAccount
from domain.purchase import PurchaseTransaction
from domain.payment import PaymentTransaction
from domain.penalty import PenaltyTransaction
from domain.bonus import BonusTransaction


def show_menu():
    print("""
1. Покупка
2. Платёж
3. Штраф
4. Бонус
5. Показать состояние
6. Выход
""")


def show_summary(account: CreditAccount):
    print("\n--- СОСТОЯНИЕ СЧЁТА ---")
    print(f"Долг: {account.debt}")
    print(f"Доступный кредит: {account.available_credit}")
    print(f"Бонусы: {account.bonuses}")
    print(f"Штрафы: {account.penalties}")
    print(f"Количество операций: {len(account.history)}")
    print("----------------------\n")


def main():
    account = CreditAccount(credit_limit=1000, credit_limit_base=1000)
    print("Кредитная карта создана. Лимит = 1000")

    while True:
        show_menu()
        choice = input("Выберите пункт: ")

        try:
            if choice == "1":
                amount = float(input("Сумма покупки: "))
                discount = float(input("Скидка (0..1): "))
                bonus = float(input("Бонус (0..1): "))

                tr = PurchaseTransaction(
                    amount=amount,
                    date=datetime.now(),
                    category="Purchase",
                    description="Console purchase",
                    discount_percent=discount,
                    bonus_percent=bonus
                )

                account.add_transaction(tr)
                print("Покупка успешно добавлена")

            elif choice == "2":
                amount = float(input("Сумма платежа: "))

                tr = PaymentTransaction(
                    amount=amount,
                    date=datetime.now(),
                    category="Payment",
                    description="Console payment"
                )

                account.add_transaction(tr)
                print("Платёж успешно добавлен")

            elif choice == "3":
                amount = float(input("Сумма штрафа: "))

                tr = PenaltyTransaction(
                    amount=amount,
                    date=datetime.now(),
                    category="Penalty",
                    description="Console penalty"
                )

                account.add_transaction(tr)
                print("Штраф добавлен")

            elif choice == "4":
                amount = float(input("Сумма бонусов: "))

                tr = BonusTransaction(
                    amount=amount,
                    date=datetime.now(),
                    category="Bonus",
                    description="Console bonus"
                )

                account.add_transaction(tr)
                print("Бонусы добавлены")

            elif choice == "5":
                show_summary(account)

            elif choice == "6":
                print("Выход")
                break

            else:
                print("Неверный пункт меню")

        except Exception as e:
            print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()
