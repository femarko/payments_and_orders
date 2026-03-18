from pydantic import BaseModel

from payments.domain.enums import (
    Currency,
    PaymentType
)
from payments.domain.value_objects import OrderId


class NewPaymentInput(BaseModel):
    order_id: str
    payment_type: PaymentType
    amount: str
    currency: Currency


class MessageResponse(BaseModel):
    message: str
