from pydantic import BaseModel

from payments.domain.enums import (
    Currency,
    PaymentType,
)



class DepositPaymentRequest(BaseModel):
    payment_id: str
    order_id: str
    payment_type: PaymentType
    amount: str
    currency: Currency
