import pytest
from datetime import datetime
from decimal import Decimal

from payments.domain.entities.payment import Payment
from payments.domain.enums import (
    PaymentStatus,
    PaymentType,
    Currency,
)
from payments.domain.value_objects import (
    OrderId,
    PaymentId,
    Money,
)
from payments.domain.errors import (
    ErrorCode,
    PaymentError,
    DomainAttributeError,
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
    with pytest.raises(DomainAttributeError) as e:
        payment.status = PaymentStatus.EXECUTED
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Direct modification of this attribute is forbidden. "
        f"Use domain methods instead. Domain methods: `update_bank_status`."
    )


def test_set_is_accepted_flag_externally_raises_attribute_error(payment_params_fixt):
    payment = Payment.create(**payment_params_fixt)
    with pytest.raises(DomainAttributeError) as e:
        payment.is_accepted = True
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Direct modification of this attribute is forbidden. "
        f"Use domain methods instead. Domain methods: `mark_as_accepted`."
    )


def test_set_is_refunded_flag_externally_raises_attribute_error(payment_params_fixt):
    payment = Payment.create(**payment_params_fixt)
    with pytest.raises(DomainAttributeError) as e:
        payment.is_refunded = True
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Direct modification of this attribute is forbidden. "
        f"Use domain methods instead. Domain methods: `mark_as_refunded`."
    )


def test_update_bank_status_changes_payment_status_and_updated_at_value(payment_params_fixt):
    payment = Payment.create(**payment_params_fixt)
    status_init = payment.status
    updated_at_init = payment.updated_at
    payment.update_bank_status(status=PaymentStatus.EXECUTED)
    status_new = payment.status
    updated_at_new = payment.updated_at
    assert status_init == PaymentStatus.CREATED
    assert status_new == PaymentStatus.EXECUTED
    assert updated_at_init is None
    assert isinstance(updated_at_new, datetime)


def test_update_bank_status_of_non_bank_payment_raises_error(order_id):
    payment = Payment.create(
        PaymentType.CASH,
        Money(Decimal("100"), Currency.RUB),
        order_id
    )
    payment.type = PaymentType.CASH
    payment._status = PaymentStatus.EXECUTED
    with pytest.raises(PaymentError) as e:
        payment.update_bank_status(PaymentStatus.EXECUTED)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == f"Unacceptable payment type: `{payment.type}`"

