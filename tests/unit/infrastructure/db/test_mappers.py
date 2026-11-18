import pytest
from datetime import (
    datetime,
    timezone,
)
from uuid import UUID, uuid4
from decimal import (
    Decimal,
    ROUND_HALF_UP
)

from payments.infrastructure.db.mappers import (
    payment_to_model,
    payment_to_entity,
    order_to_model,
    order_to_entity,
    update_payment_model,
    update_order_model,
)
from payments.domain.entities.payment import Payment
from payments.domain.entities.order import Order
from payments.infrastructure.db.orm_models import (
    SQLAlchPaymentModel,
    SQLAlchOrderModel,
)
from payments.domain.value_objects import (
    Money,
    MoneyConfig,
    OrderId,
    PaymentId
)
from payments.domain.enums import (
    Currency,
    PaymentStatus,
    OrderStatus,
    PaymentType,
)


@pytest.fixture
def params() -> dict[str, UUID | str | float | datetime]:
    return dict(
        payment_id = uuid4(),
        currency="USD",
        amount = 100.42,
        order_id = uuid4(),
        created_at = datetime(2026, 3, 20, tzinfo=timezone.utc),
        updated_at = datetime.now(timezone.utc),
        external_id = "external_id"
    )


def test_payment_to_entity_converts_orm_model_to_domain_entity(params):
    
    model = SQLAlchPaymentModel(
        id=params["payment_id"],
        type="cash",
        status="created",
        amount=params["amount"],
        currency=params["currency"],
        order_id=params["order_id"],
        created_at=params["created_at"],
        updated_at=params["updated_at"],
        external_id=params["external_id"],
        is_accepted=False,
    )

    entity = payment_to_entity(model)

    assert entity.id == PaymentId(params["payment_id"])
    assert entity.type == PaymentType.CASH
    assert entity.status == PaymentStatus.CREATED 
    assert entity.money == Money(Decimal(100.42), Currency.USD)
    assert entity.order_id == OrderId(params["order_id"])
    assert entity.created_at == params["created_at"]
    assert entity.updated_at == params["updated_at"]
    assert entity.external_id == params["external_id"]
    assert entity._is_accepted is False
    

def test_payment_to_model_converts_domain_entity_to_orm_model(params):

    entity = Payment.restore(
        id=PaymentId(params["payment_id"]),
        type=PaymentType.CASH,
        status=PaymentStatus.CREATED,
        money=Money(Decimal(params["amount"]), Currency.USD),
        order_id=OrderId(params["order_id"]),
        created_at=params["created_at"],
        updated_at=params["updated_at"],
        external_id=params["external_id"],
        is_accepted=False,
    )

    model = payment_to_model(entity)

    assert model.id == entity.id.value
    assert model.type == "cash"
    assert model.status == PaymentStatus.CREATED 
    assert model.amount == Decimal(100.42).quantize(
        MoneyConfig.QUANT, rounding=ROUND_HALF_UP
    )
    assert model.currency == "USD"
    assert model.order_id == OrderId(params["order_id"]).value
    assert model.created_at == params["created_at"]
    assert model.updated_at == params["updated_at"]
    assert model.external_id == params["external_id"]
    assert model.is_accepted is False


def test_update_payment_model_changes_orm_model(params):
    model = SQLAlchPaymentModel(
        id=params["payment_id"],
        type="cash",
        status="created",
        amount=params["amount"],
        currency=params["currency"],
        order_id=params["order_id"],
        created_at=params["created_at"],
        updated_at=params["updated_at"],
        external_id=params["external_id"],
        is_accepted=False,
    )
    initial_model_params = [
        model.id == params["payment_id"],
        model.type == "cash",
        model.status == "created",
        model.amount == params["amount"],
        model.currency == params["currency"],
        model.order_id == params["order_id"],
        model.created_at == params["created_at"],
        model.updated_at == params["updated_at"],
        model.external_id == params["external_id"],
        model.is_accepted == False
    ]
    entity = Payment.restore(
        id=PaymentId(model.id),
        type=model.type,
        status=model.status,
        money=Money(model.amount, model.currency),
        order_id=OrderId(model.order_id),
        created_at=model.created_at,
        updated_at=model.updated_at,
        external_id=model.external_id,
        is_accepted=model.is_accepted,
    )
    new_time_stamp = datetime.now(timezone.utc)
    entity.type = PaymentType.ACQUIRING
    entity.update_bank_status(PaymentStatus.EXECUTED)
    entity._mark_as_accepted(new_time_stamp)
    upated_model = update_payment_model(entity, model)
    updated_model_params = [
        upated_model.id == entity.id.value,
        upated_model.type == "acquiring",
        upated_model.status == "executed",
        upated_model.amount == entity.money.amount,
        upated_model.currency == entity.money.currency,
        upated_model.order_id == entity.order_id.value,
        upated_model.created_at == entity.created_at,
        upated_model.updated_at == entity.updated_at,
        upated_model.external_id == entity.external_id,
        upated_model.is_accepted == True,
    ]
    assert all(initial_model_params)
    assert all(updated_model_params)


def test_order_to_entity_converts_orm_model_to_domain_entity(params):
    
    model = SQLAlchOrderModel(
        id=params["order_id"],
        total_amount=params["amount"],
        currency=Currency.EUR,
        created_at=params["created_at"],
        updated_at=params["updated_at"],
        paid_amount=Decimal("50.42").quantize(
            MoneyConfig.QUANT, rounding=ROUND_HALF_UP
        )
    )

    entity = order_to_entity(model)

    assert entity.id == OrderId(params["order_id"])
    assert entity.total_amount == Money(params["amount"], Currency.EUR)
    assert entity.status == OrderStatus.PARTIALLY_PAID 
    assert entity.created_at == params["created_at"]
    assert entity.updated_at == params["updated_at"]
    assert entity.paid_amount == Money(
        Decimal("50.42").quantize(
            MoneyConfig.QUANT, rounding=ROUND_HALF_UP
        ),
        Currency.EUR)


def test_order_to_model_converts_domain_entity_to_orm_model():
    
    entity = Order(money=Money(Decimal("100"), Currency.EUR))
    entity_id = entity.id.value
    entity_money = entity.total_amount
    entity_created_at = entity.created_at
    entity_updated_at = entity.updated_at
    
    model = order_to_model(entity)

    assert model.id == entity_id
    assert model.total_amount == entity_money.amount
    assert model.created_at == entity_created_at
    assert model.updated_at == entity_updated_at
    assert model.paid_amount == Money.zero(Currency.EUR).amount


def test_update_order_model_changes_orm_model(params):
    model = SQLAlchOrderModel(
        id=params["order_id"],
        total_amount=params["amount"],
        currency=params["currency"],
        created_at=params["created_at"],
        updated_at=None,
        paid_amount=Decimal("0").quantize(
            MoneyConfig.QUANT, rounding=ROUND_HALF_UP
        )
    )
    initial_model_params = [
        model.id == params["order_id"],
        model.total_amount == params["amount"],
        model.currency == params["currency"],
        model.created_at,
        model.updated_at is None,
        model.paid_amount == Decimal("0").quantize(
            MoneyConfig.QUANT, rounding=ROUND_HALF_UP
        )
    ]
    entity = Order.restore(
        id=model.id,
        total_amount=Money(model.total_amount, model.currency),
        paid_amount=Money(model.paid_amount, model.currency),
        created_at=model.created_at,
        updated_at=model.updated_at
    )
    payment = Payment.create(
        payment_type=PaymentType.CASH,
        money=Money(params["amount"], model.currency),
        order_id=entity.id,)
    entity.accept_payment(payment)
    updated_model = update_order_model(entity, model)
    updated_model_params = [
        updated_model.id == params["order_id"],
        float(updated_model.total_amount) == params["amount"],
        updated_model.currency == params["currency"],
        updated_model.created_at == params["created_at"],
        isinstance(updated_model.updated_at, datetime),
        updated_model.paid_amount == model.total_amount
    ]
    assert all(initial_model_params)
    assert all(updated_model_params)
