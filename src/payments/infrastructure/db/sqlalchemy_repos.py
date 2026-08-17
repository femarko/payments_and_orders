from typing import (
    Optional,
    Callable,
)
from sqlalchemy import orm
from uuid import UUID

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
from payments.domain.errors import NotFoundError



class PaymentRepo:
    def __init__(
            self,
            session: ORMSessionProto[SQLAlchPaymentModel],
            to_model: Callable[[Payment], SQLAlchPaymentModel],
            to_entity: Callable[[SQLAlchPaymentModel], Payment],
            update_model: Callable[[Payment, SQLAlchPaymentModel], SQLAlchPaymentModel],
    ) -> None:
        self.session = session
        self._models: dict[UUID, SQLAlchPaymentModel] = {}
        self._to_model = to_model
        self._to_entity = to_entity
        self._update_model = update_model
   
    def add(self, entity: Payment) -> None:
        orm_model: SQLAlchPaymentModel = self._to_model(entity)
        self.session.add(orm_model)
        self._models |= {orm_model.id: orm_model}

    def get_by_id(self, payment_id: PaymentId | str) -> Optional[Payment]:
        id_parsed: str = str(payment_id.value) if isinstance(payment_id, PaymentId) else payment_id
        orm_model = self.session.get(SQLAlchPaymentModel, id_parsed)
        if not orm_model:
            return
        entity = self._to_entity(orm_model)
        self._models |= {orm_model.id: orm_model}
        return entity

    def delete(self, entity: Payment) -> None:
        orm_model = self.session.get(SQLAlchPaymentModel, str(entity.id.value))
        if orm_model:
            self.session.delete(orm_model)
            if orm_model.id in self._models:
                del self._models[orm_model.id]

    def update_model(self, entity: Payment, model_id: PaymentId) -> None:
        try:
            orm_model = self._models[model_id.value]
        except KeyError as e:
            raise NotFoundError from e
        self._update_model(entity, orm_model)


class OrderRepo:
    def __init__(
            self,
            session: ORMSessionProto[SQLAlchOrderModel],
            to_model: Callable[[Order], SQLAlchOrderModel],
            to_entity: Callable[[SQLAlchOrderModel], Order],
            update_model: Callable[[Order, SQLAlchOrderModel], SQLAlchOrderModel],
    ) -> None:
        self.session = session
        self._models: dict[UUID, SQLAlchOrderModel] = {}
        self._to_model = to_model
        self._to_entity = to_entity
        self._update_model = update_model
   
    def add(self, entity: Order) -> None:
        orm_model: SQLAlchOrderModel = self._to_model(entity)
        self.session.add(orm_model)
        self._models |= {orm_model.id: orm_model}

    def get_by_id(self, order_id: OrderId) -> Optional[Order]:
        id_parsed: str = str(order_id.value) if isinstance(order_id, OrderId) else order_id
        orm_model = self.session.get(SQLAlchOrderModel, id_parsed)
        if not orm_model:
            return
        entity = self._to_entity(orm_model)
        self._models |= {orm_model.id: orm_model}
        return entity

    def delete(self, entity: Order) -> None:
        orm_model = self.session.get(SQLAlchOrderModel, str(entity.id.value))
        if orm_model:
            self.session.delete(orm_model)
            if orm_model.id in self._models:
                del self._models[orm_model.id]

    def update_model(self, entity: Order, model_id: OrderId) -> None:
        try:
            orm_model = self._models[model_id.value]
        except KeyError as e:
            raise NotFoundError from e
        self._update_model(entity, orm_model)
