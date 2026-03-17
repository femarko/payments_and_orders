import pytest
from decimal import Decimal

from payments.domain.entities import Payment
from payments.domain.enums import (
    PaymentType,
    PaymentStatus,
    Currency,
)
from payments.domain.value_objects import (
    OrderId,
    Money,
)



@pytest.fixture
def order_id_fixt():
     return OrderId.new()


@pytest.fixture
def payment_fixt(request) -> Payment:
    payment = Payment.create(
        payment_type=request.param.get("payment_type", PaymentType.ACQUIRING),
        money=request.param.get("money", Money(Decimal("100"), Currency.RUB)),
        # order_id=request.param.get("order_id", OrderId.new()),
    )
    payment._status = request.param.get("payment_status", PaymentStatus.CREATED)
    return payment


@pytest.fixture
def payment_params_fixt() -> dict[str, PaymentType | Money | OrderId]:
    return {
        "payment_type": PaymentType.ACQUIRING,
        "money": Money(100),
        # "order_id": OrderId.new()
    }
