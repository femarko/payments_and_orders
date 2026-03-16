from typing import Callable

from payments.domain.entities import Payment
from payments.domain.repositories import UoWProto
from payments.domain.value_objects import (
    OrderId,
    PaymentId,
    Money
)


class PayOrder():
    def __init__(self, uow: Callable[..., UoWProto]) -> None:
        self.uow = uow
        
    def execute(self, order_id: OrderId):
        with self.uow() as uow:
            payment = uow.payments.model_cls.create(
                
            )
            order = uow.orders.get_by_db_id(order_id.value)
