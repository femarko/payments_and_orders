from dataclasses import dataclass
from typing import Callable

from payments.domain.entities.payment import Payment
from payments.domain.entities.order import Order
from payments.domain.value_objects import (
    PaymentId,
    OrderId,
    Money,
)
from payments.infrastructure.db.orm_models import (
    SQLAlchPaymentModel,
    SQLAlchOrderModel
)
from tests.conftest import order_id



def payment_to_model(entity: Payment) -> SQLAlchPaymentModel:
    return SQLAlchPaymentModel(
        id=entity.id.value,
        type=entity.type.value,
        status=entity.status.value,
        amount=entity.money.amount,
        currency=entity.money.currency.value,
        order_id=entity.order_id.value,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        external_id=entity.external_id,
        is_accepted=entity._is_accepted,
        is_refunded=entity._is_refunded,
        accepted_at=entity._accepted_at,
        refunded_at=entity._refunded_at
    )


def payment_to_entity(orm_model: SQLAlchPaymentModel) -> Payment:
    return Payment.restore(
        id=PaymentId(orm_model.id),
        type=orm_model.type,
        status=orm_model.status,
        money=Money(orm_model.amount, orm_model.currency),
        order_id=OrderId(orm_model.order_id),
        created_at=orm_model.created_at,
        updated_at=orm_model.updated_at,
        external_id=orm_model.external_id,
        is_accepted=orm_model.is_accepted,
        is_refunded=orm_model.is_refunded,
        accepted_at=orm_model.accepted_at,
        refunded_at=orm_model.refunded_at
    )


def order_to_model(entity: Order) -> SQLAlchOrderModel:
    return SQLAlchOrderModel(
        id=entity.id.value,
        total_amount=entity.total_amount.amount,
        currency=entity.total_amount.currency,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        paid_amount=entity.paid_amount.amount,
    )


def order_to_entity(orm_model: SQLAlchOrderModel) -> Order:
    order = Order(
        id=OrderId(orm_model.id),
        total_amount=Money(orm_model.total_amount, orm_model.currency),
        created_at=orm_model.created_at,
        updated_at=orm_model.updated_at,        
    )
    order._paid_amount = Money(orm_model.paid_amount, orm_model.currency)
    return order
  