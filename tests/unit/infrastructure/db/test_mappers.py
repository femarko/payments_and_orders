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
        is_refunded=False,
        accepted_at=None,
        refunded_at=None
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
    assert entity._is_refunded is False
    assert entity._accepted_at is None
    assert entity._refunded_at is None
    

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
        is_refunded=False,
        accepted_at=None,
        refunded_at=None
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
    assert model.is_refunded is False
    assert model.accepted_at is None
    assert model.refunded_at is None


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


def test_order_to_model_converts_domain_entity_to_orm_model(params):
    
    entity = Order(
        id=OrderId(params["order_id"]),
        total_amount=Money(params["amount"], Currency.EUR),
    )
    entity.created_at = params["created_at"]
    entity.updated_at = params["updated_at"]
    
    model = order_to_model(entity)

    assert model.id == OrderId(params["order_id"]).value
    assert model.total_amount == Money(params["amount"], Currency.EUR).amount
    assert model.created_at == params["created_at"]
    assert model.updated_at == params["updated_at"]
    assert model.paid_amount == Money.zero(Currency.EUR).amount