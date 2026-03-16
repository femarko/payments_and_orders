import pytest
from datetime import date, datetime

from payments.domain.entities import Payment
from payments.domain.enums import (
    PaymentStatus,
    PaymentType,
)
from payments.domain.value_objects import (
    OrderId,
    PaymentId,
)
from payments.domain.errors import PaymentError



def test_create_returns_payment_with_expected_attributes(payment_params):
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


def test_set_status_externally_raises_attribute_error(payment_params):
    payment = Payment.create(**payment_params)
    with pytest.raises(AttributeError):
        payment.status = PaymentStatus.REFUNDED


def test_deposit_changes_payment_status_and_updated_at_value(payment_params):
    payment = Payment.create(**payment_params)
    status_init = payment.status
    updated_at_init = payment.updated_at
    payment.deposit()
    status_new = payment.status
    updated_at_new = payment.updated_at
    assert status_init == PaymentStatus.CREATED
    assert status_new == PaymentStatus.DEPOSITED
    assert updated_at_init is None
    assert isinstance(updated_at_new, datetime)


@pytest.mark.parametrize(
        "payment",
        [
            {"payment_status": PaymentStatus.DEPOSITED},
            {"payment_status": PaymentStatus.REFUNDED}
        ],
        indirect=True,
        ids=["deposited", "refunded"]
)
def test_deposit_with_wrong_payment_status_raises_domain_error(payment):
    with pytest.raises(PaymentError):
        payment.deposit()


def test_refund_changes_payment_status_and_updated_at_value(payment_params):
    payment = Payment.create(**payment_params)
    payment.deposit()
    status_init = payment.status
    updated_at_init = payment.updated_at
    payment.refund()
    status_new = payment.status
    updated_at_new = payment.updated_at
    assert status_init == PaymentStatus.DEPOSITED
    assert status_new == PaymentStatus.REFUNDED
    assert all(
        (
            isinstance(updated_at_init, datetime),
            isinstance(updated_at_new, datetime),
            updated_at_init < updated_at_new
        )
    )


@pytest.mark.parametrize(
        "payment",
        [
            {"payment_status": PaymentStatus.CREATED, "expected": "Payment is not deposited"},
            {"payment_status": PaymentStatus.REFUNDED, "expected": "Payment is already refunded"},
            {"payment_status": "Invalid", "expected": "Invalid payment status: `Invalid`"},
        ],
        indirect=True,
        ids=["created", "refunded", "unexpected"]
)
def test_refund_with_wrong_payment_status_raises_domain_error(payment, request):
    expected = request.node.callspec.params["payment"]["expected"]
    with pytest.raises(PaymentError, match=expected):
        payment.refund()
