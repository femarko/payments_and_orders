from dataclasses import dataclass
from datetime import (
    datetime,
    timezone
)
from typing import (
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
from payments.domain.errors import (
    PaymentError,
    ErrorCode
)



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
    def status(self, value: PaymentStatus) -> None:
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
        now = datetime.now(timezone.utc)
        payment.id = PaymentId.new()
        payment.type = payment_type
        payment._status = PaymentStatus.CREATED
        payment.money = money
        payment.order_id = order_id
        payment.created_at = now
        return payment

    def deposit(self) -> None:
        if self._status != PaymentStatus.CREATED:
            raise PaymentError(
                code=ErrorCode.FORBIDDEN_OPERATION,
                message=f"Deposit is forbidden, payment status: `{self.status}`"
            )
        self._status = PaymentStatus.DEPOSITED
        self.updated_at = datetime.now(timezone.utc)

    def refund(self) -> None:
        match self._status:
            case PaymentStatus.DEPOSITED:
                self._status = PaymentStatus.REFUNDED
                self.updated_at = datetime.now(timezone.utc)        
            case PaymentStatus.REFUNDED:
                raise PaymentError(
                    code=ErrorCode.FORBIDDEN_OPERATION,
                    message="Payment is already refunded"
                )
            case PaymentStatus.CREATED:
                raise PaymentError(
                    code=ErrorCode.FORBIDDEN_OPERATION,
                    message="Payment is not deposited"
                )
            case _:
                raise PaymentError(
                    code=ErrorCode.FORBIDDEN_OPERATION,
                    message=f"Invalid payment status: `{self._status}`"
                )
