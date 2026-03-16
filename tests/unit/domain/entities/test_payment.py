
import pytest
from datetime import datetime

from payments.domain.entities import (
    Payment,
)
from payments.domain.enums import (
    Currency,
    PaymentStatus,
    OrderStatus,
    PaymentType,
)
from payments.domain.value_objects import (
    Money,
    OrderId,
    PaymentId,
    
)
from payments.domain.entities import Payment
from payments.domain.enums import PaymentStatus, PaymentType
from payments.domain.value_objects import Money, OrderId
from payments.domain.errors import PaymentError


def test_create_returns_payment_with_expected_attributes():
    payment_params = {
        "payment_type": PaymentType.ACQUIRING,
        "money": Money(100, Currency.RUB),
        "order_id": OrderId.new()
    }
    payment = Payment.create(**payment_params)
    assert isinstance(payment, Payment)
    assert isinstance(payment.id, PaymentId)
    assert isinstance(payment.type, PaymentType)
    assert payment.type == payment_params["payment_type"]
    assert payment.status == PaymentStatus.CREATED
    assert payment.money == payment_params["money"]
    assert payment.money.currency == payment_params["money"].currency
    assert payment.order_id == payment_params["order_id"]
    assert isinstance(payment.order_id, OrderId)
    assert isinstance(payment.created_at, datetime)


def test_init_raises_type_error(payment_params):
    with pytest.raises(TypeError):
        payment = Payment(**payment_params)

def test_deposit_changes_payment_status_from_created_to_deposited(payment_params):
    payment = Payment.create(**payment_params)
    initial_status = payment.status
    payment.deposit()
    new_status = payment.status
    assert initial_status == PaymentStatus.CREATED
    assert new_status == PaymentStatus.DEPOSITED


@pytest.mark.parametrize(
        "payment",
        [
            {"payment_status": PaymentStatus.DEPOSITED},
            {"payment_status": PaymentStatus.REFUNDED}
        ],
        indirect=True,
        ids=["deposited", "refunded"]
)
def test_deposit_with_wrong_payment_status_raises_error(payment):
    with pytest.raises(PaymentError):
        payment.deposit()
