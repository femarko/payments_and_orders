from pydantic import (
    BaseModel,
    field_validator
)
from uuid import UUID
from typing import TypeVar

from payments.domain.enums import (
    Currency,
    PaymentType
)
from payments.domain.value_objects import (
    OrderId,
    PaymentId,
)



class BaseUCResponse(BaseModel): ...


TResponse = TypeVar("TResponse", bound=BaseUCResponse)


class PaymentParams(BaseUCResponse):
    id: PaymentId
    order_id: OrderId
    payment_type: PaymentType
    amount: str
    currency: Currency

    @field_validator("order_id", mode="before")
    @classmethod
    def parse_order_id(cls, v) -> OrderId:
        if isinstance(v, OrderId):
            return v
        if isinstance(v, str):
            return OrderId(UUID(v))
        raise TypeError(f"Unsupported type for order_id: {type(v)}")


class MessageResponse(BaseUCResponse):
    message: str
