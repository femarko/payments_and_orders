from dataclasses import (
    dataclass,
    field,
)
from typing import Optional
from datetime import (
    datetime,
    timezone
)
from decimal import Decimal

from payments.domain.entities import BaseEntitiy
from payments.domain.entities.payment import Payment
from payments.domain.enums import (
    OrderStatus,
    PaymentStatus
)
from payments.domain.errors import (
    DomainAttributeError,
    ErrorCode,
    OrderError,
    PaymentError,
)
from payments.domain.value_objects import (
    Money,
    OrderId
)



@dataclass
class Order(BaseEntitiy):
    """
    Aggregate root representing an order and its payment state.

    Why:
    Ensures financial consistency of order payments.

    Consistency boundary:
    - all payment acceptance and refund operations must go through Order

    Invariants:
    - paid_amount <= total_amount
    - only matching currency payments allowed
    - payment must belong to the order
    """
    id: OrderId
    total_amount: Money
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        self._paid_amount = Money(Decimal("0"), self.total_amount.currency)

    @property
    def paid_amount(self) -> Money:
        """
        Total amount of accepted payments.
        """
        return self._paid_amount
    
    @paid_amount.setter
    def paid_amount(self, value: Money) -> None:
        domain_methods = "`accept_payment`, `refund_payment`"
        raise DomainAttributeError(domain_methods=domain_methods)

    @property
    def unpaid_amount(self) -> Money:
        """
        Remaining amount to be paid (read-only).
        """
        return self.total_amount - self.paid_amount
    
    @unpaid_amount.setter
    def unpaid_amount(self, value: Money) -> None:
        domain_methods = "`accept_payment`, `refund_payment`"
        raise DomainAttributeError(domain_methods=domain_methods)

    @property
    def status(self) -> OrderStatus:
        """
        Current order status (read-only).
        Derived from paid_amount.
        """
        if self.paid_amount == Money.zero(self.total_amount.currency):
            return OrderStatus.UNPAID
        elif self.paid_amount == self.total_amount:
            return OrderStatus.PAID
        else:
            return OrderStatus.PARTIALLY_PAID

    @status.setter
    def status(self, value: OrderStatus) -> None:
        domain_methods = "`accept_payment`, `refund_payment`"
        raise DomainAttributeError(domain_methods=domain_methods)

    def _validate_payment_to_order_relation(self, payment: Payment):
        """
        Ensures payment belongs to this order.
        """
        if self.id != payment.order_id:
            code = ErrorCode.FORBIDDEN_OPERATION
            message = (
                f"Incorrect order ID in payment credentials "
                f"order: id={self.id}, payment: order_id={payment.order_id}"
            )
            raise PaymentError(code, message)

    def _validate_currency(self, money: Money):
        """
        Ensures payment currency matches order currency.
        """
        if money.currency != self.total_amount.currency:
            code = ErrorCode.FORBIDDEN_OPERATION
            message = (
                f"Currency mismatch. Payment currency: `{money.currency}`, "
                f"order currency: `{self.total_amount.currency}`."
            )
            raise PaymentError(code, message)

    def _validate_payment_for_acceptance(self, payment: Payment) -> None:
        """
        Validates that payment can be accepted.

        Why:
        Prevents overpayment and inconsistent order state.

        Rules:
        - payment belongs to the order
        - currency matches
        - order is not fully paid
        - payment does not exceed unpaid amount
        """
        self._validate_payment_to_order_relation(payment)
        self._validate_currency(payment.money)
        if payment.status != PaymentStatus.EXECUTED:
            code=ErrorCode.FORBIDDEN_OPERATION
            message=f"Unacceptable payment status: `{payment.status}`"
            raise PaymentError(code, message)
        if payment.is_accepted:
            code=ErrorCode.FORBIDDEN_OPERATION
            message="Payment has already been accepted"
            raise PaymentError(code, message)

    def _validate_order_can_accept_payment(self, payment: Payment) -> None:
        if self.status == OrderStatus.PAID:
            code=ErrorCode.FORBIDDEN_OPERATION
            message="Order is already paid"
            raise PaymentError(code, message)
        if payment.money > self.unpaid_amount:
            code=ErrorCode.FORBIDDEN_OPERATION
            message=(
                f"Payment amount `{payment.money.amount}` "
                f"exceeds unpaid amount `{self.unpaid_amount.amount}`."
            )
            raise PaymentError(code, message)

    def _validate_payment_for_refund(self, payment: Payment):
        """
        Validates that payment can be refunded.

        Why:
        Prevents invalid balance changes and negative paid amount.

        Rules:
        - payment belongs to the order
        - not already refunded
        - currency matches
        - order has paid amount
        - refund does not exceed paid amount
        """
        self._validate_payment_to_order_relation(payment)
        self._validate_currency(payment.money)
        if payment.status != PaymentStatus.EXECUTED:
            code=ErrorCode.FORBIDDEN_OPERATION
            message=f"Unacceptable payment status: `{payment.status}`"
            raise PaymentError(code, message)
        if payment.is_refunded:
            code=ErrorCode.FORBIDDEN_OPERATION
            message="Payment has already been refunded"
            raise PaymentError(code, message)
        if not payment.is_accepted:
            code=ErrorCode.FORBIDDEN_OPERATION
            message="Payment has not been accepted"
            raise PaymentError(code, message)

    def _validate_order_can_refund_payment(self, payment: Payment) -> None:
        if self.status == OrderStatus.UNPAID:
            code=ErrorCode.FORBIDDEN_OPERATION
            message="Order is not paid"
            raise PaymentError(code, message)
        if payment.money > self.paid_amount:
            code=ErrorCode.FORBIDDEN_OPERATION
            message=(
                f"Amount to refund is: `{payment.money.amount}`. "
                f"This exceeds amount paid: `{self.paid_amount.amount}`"
            )
            raise OrderError(code, message)

    def accept_payment(self, payment :Payment) -> None:
        """
        Accepts payment and adds its amount to the order.

        Why:
        Order is the consistency boundary and must control
        all balance changes.

        Flow:
        - validate payment state
        - validate order invariants
        - increase paid_amount
        - mark payment as accepted
        """
        self._validate_payment_for_acceptance(payment)
        self._validate_order_can_accept_payment(payment)
        self._paid_amount += payment.money
        self.updated_at = datetime.now(timezone.utc)
        payment._mark_as_accepted(self.updated_at)

    def refund_payment(self, payment: Payment) -> None:
        """
        Refunds payment and removes its amount from the order balance.

        Why:
        Ensures order balance is reduced only through controlled
        operations.

        Flow:
        - validate payment state
        - validate order invariants
        - decrease paid_amount
        - mark payment as refunded
        """
        self._validate_payment_for_refund(payment)
        self._validate_order_can_refund_payment(payment)
        self._paid_amount -= payment.money
        self.updated_at = datetime.now(timezone.utc)
        payment._mark_as_refunded(self.updated_at)
