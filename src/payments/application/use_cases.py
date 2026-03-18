from decimal import Decimal
from pydantic import BaseModel as pydantic_basemodel
from typing import (
    Callable,
    Generic,
    TypeVar,
)

from payments.domain.protocols import (
    Order,
    Payment,
    UoWProto
)
from payments.domain.value_objects import (
    OrderId,
    Money
)
from payments.domain.errors import NotFoundError
from payments.application.dto import NewPaymentInput



TResponse = TypeVar("TResponse", bound=pydantic_basemodel)


class BaseUseCase(Generic[TResponse]):
    def __init__(
            self,
            uow: Callable[..., UoWProto],
     ) -> None:
        self.uow = uow

    def fetch_from_db(self, uow: UoWProto, id: str, repo_name: str):
        repo = getattr(uow, repo_name)
        result = repo.get_by_db_id(id)
        if not result:
            raise NotFoundError(f"Object with {id=} is not found")
        return result


class PayOrder(BaseUseCase[TResponse]):
    def __init__(
            self, uow: Callable[..., UoWProto],
            response: type[TResponse]
    ) -> None:
        super().__init__(uow)
        self.response = response        

    def execute(self, payload: NewPaymentInput) -> TResponse:
        with self.uow() as uow:
            payment: Payment = uow.payments.model_cls.create(
                payment_type=payload.payment_type,
                money=Money(
                    amount=Decimal(payload.amount),
                    currency=payload.currency,
                ),
                order_id=OrderId.from_str(payload.order_id)
            )
            order: Order = self.fetch_from_db(uow, payload.order_id, "orders")
            order.accept_payment(payment.money)
            payment.deposit()
            uow.payments.add(payment)
            uow.commit()
            payment_id = str(payment.id)
        return self.response(message=payment_id)


class RefundPayment(BaseUseCase[TResponse]):
    def __init__(
            self, uow: Callable[..., UoWProto],
            response: type[TResponse]
    ) -> None:
        super().__init__(uow)
        self.response = response

    def execute(self, payment_id: str) -> TResponse:
        with self.uow() as uow:
            payment: Payment = self.fetch_from_db(uow, payment_id, "payments")    
            order_id = str(payment.order_id)
            order: Order = self.fetch_from_db(uow, order_id, "orders")
            order.refund_payment(payment.money)
            payment.refund()
            uow.commit()
        return self.response(message="Success")
