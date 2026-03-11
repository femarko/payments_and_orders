from enum import Enum


class PaymentType(str, Enum):
    CASH = "cash"
    ACQUIRING = "acquiring"


class OrderStatus(str, Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"


class PaymentStatus(str, Enum):
    CREATED = "created"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
