import pytest
from random import randint
from decimal import Decimal
from typing import Any

from payments.domain.entities.payment import Payment
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
def payment_fixt(request, order_id) -> Payment:
    payment = Payment.create(
        payment_type=request.param.get("payment_type", PaymentType.ACQUIRING),
        money=request.param.get("money", Money(Decimal("100"), Currency.RUB)),
        order_id=request.param.get("order_id", order_id),
    )
    payment._status = request.param.get("payment_status", PaymentStatus.CREATED)
    payment._is_accepted = request.param.get("payment_is_accepted", False)
    return payment


@pytest.fixture
def payment_params_fixt() -> dict[str, PaymentType | Money | OrderId]:
    return {
        "payment_type": PaymentType.ACQUIRING,
        "money": Money(100),
        "order_id": OrderId.new()
    }


@pytest.fixture
def fake_bank_api(bank_id: str) -> dict[str, str] | dict[str, Any]:
    if randint(1, 100) % 2 == 0:
        return {
            "bank_id": bank_id,
            "error": "Payment is not  not found"
        }
    status = None
    end = randint(1, len(PaymentStatus))
    for i, v in enumerate(PaymentStatus):
        if i == end:
            status = v
    return {
        "bank_id": bank_id,
        "amount": "100",
        "status": status,
        "transaction_date_and_time": None
    }


@pytest.fixture
def order_id():
     return OrderId.new()
