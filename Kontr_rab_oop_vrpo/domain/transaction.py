from abc import ABC, abstractmethod
from datetime import datetime


class Transaction(ABC):
    def __init__(self, amount: float, date: datetime, category: str, description: str):
        self.amount = amount
        self.date = date
        self.category = category
        self.description = description

    @abstractmethod
    def apply(self, account):
        pass

    def is_valid(self, account) -> bool:
        return True
