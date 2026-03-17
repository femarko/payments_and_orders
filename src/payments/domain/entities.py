from dataclasses import dataclass
from datetime import (
    datetime,
    timezone
)
from locale import currency
from typing import (
    Optional,
    Self
)

from payments.domain.enums import (
    PaymentStatus,
    PaymentType,
    OrderStatus,
)
from payments.domain.value_objects import (
    OrderId,
    PaymentId,
    Money,
)
from payments.domain.errors import (
    OrderStatusError,
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
    created_at: datetime
    _order_id: Optional[OrderId] = None
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
    
    @property
    def order_id(self) -> Optional[OrderId]:
        return self._order_id

    @classmethod
    def create(
        cls,
        payment_type: PaymentType,
        money: Money
    ) -> Self:
        payment = cls.__new__(cls)
        now = datetime.now(timezone.utc)
        payment.id = PaymentId.new()
        payment.type = payment_type
        payment._status = PaymentStatus.CREATED
        payment.money = money
        payment.created_at = now
        return payment

    def deposit(self, order_id: OrderId) -> None:
        if self._status != PaymentStatus.CREATED:
            raise PaymentError(
                code=ErrorCode.FORBIDDEN_OPERATION,
                message=f"Deposit is forbidden, payment status: `{self.status}`"
            )
        self._order_id = order_id
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
            

@dataclass
class Order(BaseEntity):
    id: OrderId
    total_amount: Money
    payments: list[Payment]
    _status: OrderStatus = OrderStatus.UNPAID
    
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
        return self._status

    def _update_status(self):
        if self.unpaid_amount == self.total_amount:
            self._status = OrderStatus.UNPAID
        elif self.unpaid_amount > Money.zero(self.total_amount.currency):
            self._status = OrderStatus.PARTIALLY_PAID
        elif self.unpaid_amount == Money.zero(self.total_amount.currency):
            self._status = OrderStatus.PAID
        else:
            raise OrderStatusError(
                code=ErrorCode.FORBIDDEN_OPERATION,
                message="Paid amount exceeds total amount"
            )

    def _validate_payment(self, payment: Payment) -> None:
        if self.status == OrderStatus.PAID:
            raise PaymentError(
                code=ErrorCode.FORBIDDEN_OPERATION,
                message="Order is already paid"
            )
        if payment.money > self.unpaid_amount:
            raise PaymentError(
                code=ErrorCode.FORBIDDEN_OPERATION,
                message=f"Amount {payment.money.amount} exceeds unpaid amount"
            )

    def add_payment(self, payment_type: PaymentType, money: Money) -> None:
        payment = Payment.create(payment_type, money)
        self._validate_payment(payment)
        payment.deposit(self.id)
        self.payments.append(payment)
        self._update_status()

    def refund_payment(self, payment_id: PaymentId) -> None:
        try:
            payment = next(
                filter(lambda p: p.id == payment_id, self.payments)
            )
        except StopIteration:
            raise PaymentError(
                code=ErrorCode.NOT_FOUND,
                message=f"Payment with ID `{payment_id}` is not found"
            )
        payment.refund()
        self._update_status()
