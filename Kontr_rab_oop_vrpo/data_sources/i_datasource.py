from __future__ import annotations
from abc import ABC, abstractmethod
from domain.credit_account import CreditAccount


class IDataSource(ABC):
    @abstractmethod
    def load_account(self) -> CreditAccount:
        raise NotImplementedError

    @abstractmethod
    def save_account(self, acc: CreditAccount) -> None:
        raise NotImplementedError
