from pydantic import BaseModel

from src.payments.domain.enums import (
    Currency,
    PaymentType
)



class NewPaymentInput(BaseModel):
    order_id: str
    payment_type: PaymentType
    amount: str
    currency: Currency


class MessageResponse(BaseModel):
    message: str
