from typing import (
    Optional,
    Callable,
)

from sqlalchemy import orm

from payments.application.interfaces.uow_interface import ORMSessionProto
from payments.domain.entities.payment import Payment
from payments.domain.entities.order import Order
from payments.domain.entities import T_Domain_Entity
from payments.infrastructure.db.orm_models import (
    SQLAlchOrderModel,
    SQLAlchPaymentModel,
)
from payments.domain.value_objects import (
    PaymentId,
    OrderId,
) 



class PaymentRepo:
    def __init__(
            self,
            session: ORMSessionProto[SQLAlchPaymentModel],
            to_model: Callable[[Payment], SQLAlchPaymentModel],
            to_entity: Callable[[SQLAlchPaymentModel], Payment],
    ) -> None:
        self.session = session
        self._to_model = to_model
        self._to_entity = to_entity
   
    def add(self, entity: Payment) -> None:
        orm_model: SQLAlchPaymentModel = self._to_model(entity)
        self.session.add(orm_model)

    def get_by_id(self, entity_id: PaymentId) -> Optional[Payment]:
        orm_model = self.session.get(SQLAlchPaymentModel, str(entity_id.value))
        if not orm_model:
            return
        entity = self._to_entity(orm_model)
        return entity

    def delete(self, entity: Payment) -> None:
        orm_model = self.session.get(SQLAlchPaymentModel, str(entity.id.value))
        if orm_model:
            self.session.delete(orm_model)


class OrderRepo:
    def __init__(
            self,
            session: ORMSessionProto[SQLAlchOrderModel],
            to_model: Callable[[Order], SQLAlchOrderModel],
            to_entity: Callable[[SQLAlchOrderModel], Order],
     ) -> None:
        self.session = session
        self._to_model = to_model
        self._to_entity = to_entity
   
    def add(self, entity: Order) -> None:
        orm_model: SQLAlchOrderModel = self._to_model(entity)
        self.session.add(orm_model)

    def get_by_id(self, entity_id: OrderId) -> Optional[Order]:
        orm_model = self.session.get(SQLAlchOrderModel, str(entity_id.value))
        if not orm_model:
            return
        entity = self._to_entity(orm_model)
        return entity

    def delete(self, entity: Order) -> None:
        orm_model = self.session.get(SQLAlchOrderModel, str(entity.id.value))
        if orm_model:
            self.session.delete(orm_model)
