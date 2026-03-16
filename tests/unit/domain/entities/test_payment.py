import pytest
from datetime import datetime

from payments.domain.entities import Payment
from payments.domain.enums import (
    PaymentStatus,
    PaymentType,
)
from payments.domain.value_objects import (
    OrderId,
    PaymentId,
)
from payments.domain.errors import (
    PaymentError,
    ErrorCode,
)



def test_create_returns_payment_with_expected_attributes(payment_params_fixt):
    payment = Payment.create(**payment_params_fixt)
    assert isinstance(payment, Payment)
    assert isinstance(payment.id, PaymentId)
    assert isinstance(payment.type, PaymentType)
    assert payment.type == payment_params_fixt["payment_type"]
    assert payment.status == PaymentStatus.CREATED
    assert payment.money == payment_params_fixt["money"]
    assert payment.money.currency == payment_params_fixt["money"].currency
    assert payment.order_id == payment_params_fixt["order_id"]
    assert isinstance(payment.order_id, OrderId)
    assert isinstance(payment.created_at, datetime)


def test_init_raises_type_error(payment_params_fixt):
    with pytest.raises(TypeError):
        payment = Payment(**payment_params_fixt)


def test_set_status_externally_raises_attribute_error(payment_params_fixt):
    payment = Payment.create(**payment_params_fixt)
    with pytest.raises(AttributeError):
        payment.status = PaymentStatus.REFUNDED


def test_deposit_changes_payment_status_and_updated_at_value(payment_params_fixt):
    payment = Payment.create(**payment_params_fixt)
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
        "payment_fixt",
        [
            {"payment_status": PaymentStatus.DEPOSITED},
            {"payment_status": PaymentStatus.REFUNDED}
        ],
        indirect=True,
        ids=["deposited", "refunded"]
)
def test_deposit_with_wrong_payment_status_raises_domain_error(payment_fixt, request):
    status_passed = request.node.callspec.params["payment_fixt"]["payment_status"]
    with pytest.raises(PaymentError, match=f"Deposit is forbidden, payment status: `{status_passed}`") as exc:
        payment_fixt.deposit()
    err = exc.value
    assert err.code == ErrorCode.FORBIDDEN_OPERATION


def test_refund_changes_payment_status_and_updated_at_value(payment_params_fixt):
    payment = Payment.create(**payment_params_fixt)
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
        "payment_fixt",
        [
            {"payment_status": PaymentStatus.CREATED, "expected": "Payment is not deposited"},
            {"payment_status": PaymentStatus.REFUNDED, "expected": "Payment is already refunded"},
            {"payment_status": "Invalid", "expected": "Invalid payment status: `Invalid`"},
        ],
        indirect=True,
        ids=["created", "refunded", "unexpected"]
)
def test_refund_with_wrong_payment_status_raises_domain_error(payment_fixt, request):
    expected = request.node.callspec.params["payment_fixt"]["expected"]
    with pytest.raises(PaymentError, match=expected):
        payment_fixt.refund()
