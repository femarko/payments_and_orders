from dataclasses import dataclass
from datetime import (
    datetime,
    timezone
)
from typing import (
    NoReturn,
    Optional,
    Self
)

from payments.domain.enums import (
    PaymentStatus,
    PaymentType,
)
from payments.domain.value_objects import (
    OrderId,
    PaymentId,
    Money,
)
from payments.domain.errors import PaymentError



@dataclass
class BaseEntity: ...


@dataclass(init=False)
class Payment(BaseEntity):
    id: PaymentId
    type: PaymentType
    _status: PaymentStatus
    money: Money
    order_id: OrderId
    created_at: datetime
    updated_at: Optional[datetime] = None
    external_id: Optional[str] = None
    
    @property
    def status(self) -> PaymentStatus:
        return self._status

    @status.setter
    def status(self, value: PaymentStatus) -> NoReturn:
        raise AttributeError(
            "Direct status modification is forbidden. "
            "Use domain methods (deposit, refund)."
        )

    @classmethod
    def create(
        cls,
        payment_type: PaymentType,
        money: Money,
        order_id: OrderId
    ) -> Self:
        payment = cls.__new__(cls)
        payment.id = PaymentId.new()
        payment.type = payment_type
        payment._status = PaymentStatus.CREATED
        payment.money = money
        payment.order_id = order_id
        payment.created_at = datetime.now(timezone.utc)
        return payment

    def deposit(self) -> None:
        if self._status != PaymentStatus.CREATED:
            raise PaymentError(
                f"Deposit is forbidden, payment status: `{self.status}`"
        )
        self._status = PaymentStatus.DEPOSITED

    def refund(self) -> None:
        if self._status == PaymentStatus.REFUNDED:
            raise PaymentError("Payment is already refunded")
        if self._status != PaymentStatus.DEPOSITED:
            raise PaymentError("Payment is not deposited")
        self._status = PaymentStatus.REFUNDED
