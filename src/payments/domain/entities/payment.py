from dataclasses import dataclass
from datetime import datetime, timezone
from typing import (
    Self,
    Optional,
    Any,
)


from payments.domain.entities import BaseEntitiy
from payments.domain.enums import (
    PaymentStatus,
    PaymentType
)
from payments.domain.errors import DomainAttributeError, ErrorCode, PaymentError
from payments.domain.value_objects import Money, OrderId, PaymentId



class Payment(BaseEntitiy):
    """
    Represents a payment in two contexts:

    1) Payment transaction lifecycle (external system / bank): status
    2) Accounting lifecycle (order balance): acceptance/refund flags

    Why:
    A payment may be successfully processed by the bank but not yet
    recognized in the order balance.

    These lifecycles are intentionally separated.

    Note:
    Deposit/refund operations are intentionally handled by Order
    (aggregate root) to maintain consistency.

    Creation and restoration are handled via factory methods.
    Invariants are enforced during creation.

    All initialization logic is handled in the factory method.
    """
    id: PaymentId
    type: PaymentType
    _status: PaymentStatus
    money: Money
    order_id: OrderId
    created_at: datetime
    updated_at: Optional[datetime] = None
    external_id: Optional[str] = None
    _is_accepted: bool = False

    @property
    def status(self) -> PaymentStatus:
        """
        Payment transaction status (read-only).
        """
        return self._status

    @status.setter
    def status(self, value: PaymentStatus) -> None:
        raise DomainAttributeError(domain_methods="`update_bank_status`")

    @property
    def is_accepted(self) -> bool:
        """
        Whether the payment is included in the order's
        paid amount (read-only).
        """
        return self._is_accepted

    @is_accepted.setter
    def is_accepted(self, value: bool) -> None:
        raise DomainAttributeError(domain_methods="`mark_as_accepted`")

    @classmethod
    def create(
        cls,
        payment_type: PaymentType,
        money: Money,
        order_id: OrderId
    ) -> Self:
        """
        Factory method for new payments.

        Initial state:
        - status = CREATED
        - not accepted
        - not refunded
        """
        payment = cls.__new__(cls)
        now = datetime.now(timezone.utc)
        payment.id = PaymentId.new()
        payment.type = payment_type
        payment._status = PaymentStatus.CREATED
        payment.money = money
        payment.order_id = order_id
        payment.created_at = now
        if payment_type == PaymentType.CASH:
            payment._status = PaymentStatus.EXECUTED
        else:
            payment._status = PaymentStatus.CREATED
        return payment

    @classmethod
    def restore(
        cls,
        id: PaymentId,
        type: PaymentType,
        status: PaymentStatus,
        money: Money,
        order_id: OrderId,
        created_at: datetime,
        updated_at: Optional[datetime],
        external_id: Optional[str],
        is_accepted: bool,
    ) -> Self:
        """
        Recreates a Payment from persisted state.
        Not intended for creating new payments.
        """
        payment = cls.__new__(cls)
        payment.id = id
        payment.type = type
        payment._status = status
        payment.money = money
        payment.order_id = order_id
        payment.created_at = created_at
        payment.updated_at = updated_at
        payment.external_id = external_id
        payment._is_accepted = is_accepted
        return payment

    def update_bank_status(self, status: PaymentStatus) -> None:
        """
        Uupdates transaction status from external (bank) system.

        Why:
        External systems may change payment state independently.

        Applicable only to acquiring payments.
        """
        if self.type != PaymentType.ACQUIRING:
            code=ErrorCode.FORBIDDEN_OPERATION
            message=f"Unacceptable payment type: `{self.type}`"
            raise PaymentError(code, message)
        self._status = status
        self.updated_at = datetime.now(timezone.utc)


    def _mark_as_accepted(self, timestamp: datetime) -> None:
        """
        Marks payment as accepted and records acceptance timestamp.
        """
        self._is_accepted = True
        self.updated_at = timestamp

    def _mark_as_refunded(self, timestamp: datetime) -> None:
        """
        Marks payment as refunded and records refund timestamp.
        """
        self._is_accepted = False
        self.updated_at = timestamp

    def params(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "money": self.money,
            "order_id": self.order_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "external_id": self.external_id,
            "is_accepted": self.is_accepted,
        }
