from dataclasses import dataclass
from decimal import Decimal
from datetime import (
    datetime,
    timezone
)
from typing import (
    Optional,
    Self,
    TypeVar
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
    OrderError,
    PaymentError,
    ErrorCode
)



class BaseEntitiy: ...
T_Domain_Entity = TypeVar("T_Domain_Entity", bound=BaseEntitiy)


@dataclass(init=False)
class Payment(BaseEntitiy):
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
        if not self.order_id:
            code = ErrorCode.INVALID_DATA
            message = "Order ID is missing"
            raise PaymentError(code, message)
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
class Order(BaseEntitiy):
    id: OrderId
    total_amount: Money
    _status: OrderStatus = OrderStatus.UNPAID
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        self._paid_amount = Money(Decimal("0"), self.total_amount.currency)

    @property
    def paid_amount(self) -> Money:
        return self._paid_amount

    @property
    def unpaid_amount(self) -> Money:
        return self.total_amount - self.paid_amount

    @property
    def status(self) -> OrderStatus:
        return self._status

    @status.setter
    def status(self, value: OrderStatus) -> None:
        raise AttributeError(
            "Direct status modification is forbidden. "
            "Use domain methods (accept_payment, refund_payment)."
        )

    def _update_status(self):
        if self.unpaid_amount == self.total_amount:
            self._status = OrderStatus.UNPAID
        elif self.unpaid_amount > Money.zero(self.total_amount.currency):
            self._status = OrderStatus.PARTIALLY_PAID
        elif self.unpaid_amount == Money.zero(self.total_amount.currency):
            self._status = OrderStatus.PAID
        else:
            raise OrderError(
                code=ErrorCode.FORBIDDEN_OPERATION,
                message="Paid amount exceeds total amount"
            )

    def _validate_currency(self, money):
        if money.currency != self.total_amount.currency:
            code = ErrorCode.FORBIDDEN_OPERATION
            message = f"Payment currency `{money.currency}` differs "
            f"from order currency `{self.total_amount.currency}`"
            raise PaymentError(code, message)

    def _validate_new_payment(self, money: Money) -> None:
        if self.status == OrderStatus.PAID:
            raise OrderError(
                code=ErrorCode.FORBIDDEN_OPERATION,
                message="Order is already paid"
            )
        self._validate_currency(money)      
        if money > self.unpaid_amount:
            raise OrderError(
                code=ErrorCode.FORBIDDEN_OPERATION,
                message=f"Amount {money.amount} exceeds unpaid amount"
            )

    def _validate_refund(self, money: Money):
        self._validate_currency(money)
        if money > self.paid_amount:
            raise OrderError(
                code=ErrorCode.FORBIDDEN_OPERATION,
                message=f"Refund amount `{money.amount}` "
                f"exceeds paid amount `{self.paid_amount}`"
            )

    def accept_payment(self, money: Money) -> None:
        self._validate_new_payment(money)
        self._paid_amount += money
        self._update_status()
        self.updated_at = datetime.now(timezone.utc)

    def refund_payment(self, money: Money) -> None:
        self._validate_refund(money)
        self._paid_amount -= money
        self._update_status()
        self.updated_at = datetime.now(timezone.utc)
