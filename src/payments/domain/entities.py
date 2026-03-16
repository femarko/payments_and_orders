from decimal import Decimal
from uuid import UUID
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
    OrderStatus,
    PaymentType,
)
from payments.domain.value_objects import (
    OrderId,
    PaymentId,
    Money,
)
from payments.domain.errors import (
    PaymentError,
    NotFoundError
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
    def status(self, value: PaymentStatus):
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


@dataclass
class Order(BaseEntity):
    id: OrderId
    total_amount: Money
    payments: list[Payment]
    
    @property
    def paid_amount(self) -> Money:
        return sum(
            (
                p.money for p in self.payments
                if p.status == PaymentStatus.DEPOSITED
            ),
            Money.zero(self.total_amount.currency)
        )
    
    @property
    def unpaid_amount(self) -> Money:
        return self.total_amount - self.paid_amount

    @property
    def status(self) -> OrderStatus:
        self.update_status()
        return self._status

    def update_status(self):
        if not self.unpaid_amount:
            self._status = OrderStatus.PAID
            return
        if self.paid_amount:
            self._status = OrderStatus.PARTIALLY_PAID
            return
        self._status = OrderStatus.UNPAID

    def _validate_payment(self, payment: Payment) -> None:
        if self.status == OrderStatus.PAID:
            raise PaymentError("Order is already paid")
        if payment.money > self.unpaid_amount:
            raise PaymentError(
                f"Amount {payment.money.amount} exceeds unpaid amount"
            )

    def add_payment(self, payment: Payment) -> None:
        self._validate_payment(payment)
        self.payments.append(payment)
        self.update_status()
    
    def refund_payment(self, payment_id: PaymentId) -> None:
        payment_to_refund = next(filter(lambda p: p.id == payment_id, self.payments))
        if not payment_to_refund:
            raise NotFoundError(f"Payment with ID `{payment_id}` is not found")        
        self.payments[self.payments.index(payment_to_refund)].refund()
