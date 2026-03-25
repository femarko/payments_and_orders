from enum import StrEnum



class PaymentType(StrEnum):
    CASH = "cash"
    ACQUIRING = "acquiring"


class OrderStatus(StrEnum):
    UNPAID = "unpaid"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"


class PaymentStatus(StrEnum):
    CREATED = "created"
    PENDING = "pending"
    EXECUTED = "executed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Currency(StrEnum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
