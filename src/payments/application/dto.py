from pydantic import (
    BaseModel,
    field_validator
)
from typing import TypeVar

from payments.domain.enums import (
    Currency,
    PaymentType
)
from payments.domain.value_objects import (
    OrderId,
    PaymentId,
    BaseId,
)



class BaseUCDTO(BaseModel): ...


TResponse = TypeVar("TResponse", bound=BaseUCDTO)
TId = TypeVar("TId", bound=BaseId)


def parse_id(
        value: object,
        id_type: type[TId]
) -> TId:
    if isinstance(value, id_type):
        return value
    if isinstance(value, str):
        return id_type.from_string(value)
    raise TypeError(f"Unsupported type for id: {type(value)}")



class PaymentParams(BaseUCDTO):
    id: PaymentId | str
    order_id: OrderId | str
    payment_type: PaymentType
    amount: str
    currency: Currency

    @field_validator("id", mode="before")
    @classmethod
    def parse_payment_id(cls, v) -> PaymentId:
        return parse_id(value=v, id_type=PaymentId)

    @field_validator("order_id", mode="before")
    @classmethod
    def parse_order_id(cls, v) -> OrderId:
        return parse_id(value=v, id_type=OrderId)
    

class MessageResponse(BaseUCDTO):
    message: str
