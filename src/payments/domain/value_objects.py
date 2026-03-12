from dataclasses import dataclass
from typing import Self
from decimal import Decimal
from uuid import (
    UUID,
    uuid4
)

from payments.domain.enums import Currency


@dataclass(frozen=True, slots=True)
class BaseId:
    value: UUID

    @classmethod
    def new(cls) -> Self:
        return cls(uuid4())
    
    def __str__(self) -> str:
        return str(self.value)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value})"


class PaymentId(BaseId): ...


class OrderId(BaseId): ...


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: Currency = Currency.RUB
