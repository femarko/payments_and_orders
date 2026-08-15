from dataclasses import dataclass
from typing import Callable

from payments.domain.entities.payment import Payment
from payments.domain.enums import (
    PaymentStatus,
    PaymentType,
    Currency,
)
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



def payment_to_model(entity: Payment) -> SQLAlchPaymentModel:
    return SQLAlchPaymentModel(
        id=entity.id.value,
        type=entity.type.value if isinstance(entity.type, PaymentType) else entity.type,
        status=entity.status.value if isinstance(entity.status, PaymentStatus) else entity.status,
        amount=entity.money.amount,
        currency=entity.money.currency.value if isinstance(entity.money.currency, Currency) else entity.money.currency,
        order_id=entity.order_id.value,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        external_id=entity.external_id,
        is_accepted=entity.is_accepted,
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


def update_payment_model(entity: Payment, orm_model: SQLAlchPaymentModel) -> SQLAlchPaymentModel:
    orm_model.type = entity.type
    orm_model.status = entity.status
    orm_model.amount = entity.money.amount
    orm_model.currency = entity.money.currency
    orm_model.order_id = entity.order_id.value
    orm_model.created_at = entity.created_at
    orm_model.updated_at = entity.updated_at
    orm_model.external_id = entity.external_id
    orm_model.is_accepted = entity.is_accepted
    orm_model.is_refunded = entity._is_refunded
    orm_model.accepted_at = entity._accepted_at
    orm_model.refunded_at = entity._refunded_at
    return orm_model


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


def update_order_model(entity: Order, orm_model: SQLAlchOrderModel) -> SQLAlchOrderModel:
    orm_model.total_amount = entity.total_amount.amount
    orm_model.currency = entity.total_amount.currency
    orm_model.created_at = entity.created_at
    orm_model.updated_at = entity.updated_at
    orm_model.paid_amount = entity.paid_amount.amount
    return orm_model
