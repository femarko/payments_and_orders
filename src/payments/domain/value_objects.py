from dataclasses import dataclass
from typing import Self
from decimal import Decimal
from functools import total_ordering
from uuid import (
    UUID,
    uuid4
)

from payments.domain.enums import Currency
from payments.domain.errors import IncompatibleCurrencyError


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


@total_ordering
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: Currency = Currency.RUB

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(self.amount))

    def _validate_currency(self, other: Self) -> None:
        if self.currency != other.currency:
            raise IncompatibleCurrencyError(self.currency.value, other.currency.value)

    def __add__(self, other: Self) -> Self:
        if not isinstance(other, Money):
            return NotImplemented
        self._validate_currency(other)
        return type(self)(self.amount + other.amount, self.currency)
    
    def __sub__(self, other: Self) -> Self:
        if not isinstance(other, Money):
            return NotImplemented
        self._validate_currency(other)
        return type(self)(self.amount - other.amount, self.currency)
          
    def __lt__(self, other: Self) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        self._validate_currency(other)
        return self.amount < other.amount

    def __bool__(self) -> bool:
        return self.amount != 0

    @classmethod
    def zero(cls, currency: Currency = Currency.RUB) -> Self:
        return cls(Decimal("0"), currency)
