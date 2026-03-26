from math import e

import pytest
from decimal import Decimal
from types import NoneType
from datetime import datetime

from redis.utils import C

from payments.domain.entities.payment import Payment
from payments.domain.entities.order import Order
from payments.domain.enums import (
    PaymentStatus,
    OrderStatus,
    Currency,
)
from payments.domain.value_objects import (
    Money,
    OrderId,
)
from payments.domain.errors import (
    DomainAttributeError,
    ErrorCode,
    PaymentError,
    OrderError,
)
from payments.domain.enums import (
    Currency,
    PaymentType
)



def make_payment(
        amount: str | int | Decimal,
        order_id: OrderId,
        currecy: Currency = Currency.RUB,

) -> Payment:
    payment = Payment.create(
        payment_type=PaymentType.ACQUIRING,
        money=Money(Decimal(amount), currecy),
        order_id=order_id,
    )
    return payment


def test_accept_payment_changes_order_and_payment_state(order_id):

    order = Order(
        id=order_id,
        total_amount=Money(Decimal("500"), Currency.RUB)
    )
    order_state_before = (
        order.status,
        order.unpaid_amount,
        order.paid_amount,
        isinstance(order.updated_at, NoneType)
    )
    
    payment = make_payment(amount="300", order_id=order_id)
    payment._status = PaymentStatus.EXECUTED
    payment_state_before = (
        payment.is_accepted,
        isinstance(payment.accepted_at, NoneType),
        isinstance(payment.updated_at, NoneType)
    )
    
    order.accept_payment(payment)
    
    order_state_after = (
        order.status,
        order.unpaid_amount,
        order.paid_amount,
        isinstance(order.updated_at, datetime)
    )
    payment_state_after = (
        payment.is_accepted,
        isinstance(payment.accepted_at, datetime),
        isinstance(payment.updated_at, datetime)
    )
    
    assert order_state_before == (
        OrderStatus.UNPAID,
        Money(Decimal("500"), Currency.RUB),
        Money.zero(Currency.RUB),
        True
    )
    assert order_state_after == (
        OrderStatus.PARTIALLY_PAID,
        Money(Decimal("200"), Currency.RUB),
        Money(Decimal("300"), Currency.RUB),
        True
    )
    assert payment_state_before == (False, True, True)
    assert payment_state_after == (True, True, True)


def test_refund_payment_changes_order_and_payment_state(order_id):
    total_amount = Money(Decimal("500"), Currency.RUB)
    order = Order(id=order_id, total_amount=total_amount)
    order._paid_amount = total_amount
    
    order_state_before = (
        order.status,
        order.unpaid_amount,
        order.paid_amount,
        isinstance(order.updated_at, NoneType)
    )
    
    payment = make_payment("300", order_id)
    payment._is_accepted = True
    payment._status = PaymentStatus.EXECUTED
    payment_state_before = (
        payment.is_refunded,
        isinstance(payment.refunded_at, NoneType),
        isinstance(payment.updated_at, NoneType)
    )

    order.refund_payment(payment)
    
    order_state_after = (
        order.status,
        order.unpaid_amount,
        order.paid_amount,
        isinstance(order.updated_at, datetime)
    )
    payment_state_after = (
        payment.is_refunded,
        isinstance(payment.refunded_at, datetime),
        isinstance(payment.updated_at, datetime)
    )

    assert order_state_before == (
        OrderStatus.PAID,
        Money.zero(Currency.RUB),
        Money(Decimal("500"), Currency.RUB),
        True
    )
    assert order_state_after == (
        OrderStatus.PARTIALLY_PAID,
        Money(Decimal("300"), Currency.RUB),
        Money(Decimal("200"), Currency.RUB),
        True
    )
    assert payment_state_before == (False, True, True)
    assert payment_state_after == (True, True, True)


def test_unpaid_amount_property_subtracts_paid_amount_from_total_amount(order_id):
    order = Order(id = order_id, total_amount=Money(Decimal("100"), Currency.RUB))
    order._paid_amount = Money(Decimal("30"), Currency.RUB)
    assert order.unpaid_amount == Money(Decimal("70"), Currency.RUB)


@pytest.mark.parametrize(
        "paid_amount, expected",
        [
            ("0", OrderStatus.UNPAID),
            ("50", OrderStatus.PARTIALLY_PAID),
            ("100", OrderStatus.PAID)
        ]
)
def test_status_property_returns_correct_value_based_on_paid_amount(
    order_id,
    paid_amount,
    expected
):
    order = Order(id = order_id, total_amount=Money(Decimal("100"), Currency.RUB))
    order._paid_amount = Money(Decimal(paid_amount), Currency.RUB)
    assert order.status == expected


def test_status_attribute_caanot_be_set_manually(order_id):
    order = Order(id = order_id, total_amount=Money(Decimal("100"), Currency.RUB))
    with pytest.raises(DomainAttributeError) as e:
        order.status = OrderStatus.PAID
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Direct modification of this attribute "
        f"is forbidden. Use domain methods instead."
        f" Domain methods: `accept_payment`, `refund_payment`."
    )


def test_paid_amount_attribute_cannot_be_set_manually(order_id):
    order = Order(id = order_id, total_amount=Money(Decimal("100"), Currency.RUB))
    with pytest.raises(DomainAttributeError) as e:
        order.paid_amount = Money(Decimal("50"), Currency.RUB)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Direct modification of this attribute "
        f"is forbidden. Use domain methods instead."
        f" Domain methods: `accept_payment`, `refund_payment`."
    )


def test_unpaid_amount_attribute_cannot_be_set_manually(order_id):
    order = Order(id = order_id, total_amount=Money(Decimal("100"), Currency.RUB))
    with pytest.raises(DomainAttributeError) as e:
        order.unpaid_amount = Money(Decimal("50"), Currency.RUB)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Direct modification of this attribute "
        f"is forbidden. Use domain methods instead."
        f" Domain methods: `accept_payment`, `refund_payment`."
    )


def test_accept_payment_with_wrong_order_id_raises_error(order_id):
    wrong_order_id = OrderId.new()
    payment = make_payment("450", wrong_order_id)
    payment._status = PaymentStatus.EXECUTED
    total_amount=Money(Decimal("400"), Currency.RUB)
    order = Order(id=order_id, total_amount=total_amount)
    with pytest.raises(PaymentError) as e:
        order.accept_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message ==  (
        f"Incorrect order ID in payment credentials "
        f"order: id={order.id}, payment: order_id={wrong_order_id}"
    )


def test_refund_payment_with_wrong_order_id_raises_error(order_id):
    wrong_order_id = OrderId.new()
    payment = make_payment("450", wrong_order_id)
    payment._status = PaymentStatus.EXECUTED
    total_amount=Money(Decimal("400"), Currency.RUB)
    order = Order(id=order_id, total_amount=total_amount)
    with pytest.raises(PaymentError) as e:
        order.refund_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Incorrect order ID in payment credentials "
        f"order: id={order.id}, payment: order_id={wrong_order_id}"
    )


def test_accept_payment_with_wrong_currency_raises_error(order_id):
    order_currecy = Currency.RUB
    payment_currency = Currency.USD
    order = Order(
        id=order_id,
        total_amount=Money(Decimal("500"), order_currecy)
    )
    payment = make_payment("450", order_id)
    payment.money = Money(Decimal("100"), payment_currency)
    payment._status = PaymentStatus.EXECUTED
    with pytest.raises(PaymentError) as e:
        order.accept_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Currency mismatch. Payment currency: `{payment_currency}`, "
        f"order currency: `{order_currecy}`."
    )


def test_refund_payment_with_wrong_currency_raises_error(order_id):
    order_currecy = Currency.RUB
    payment_currency = Currency.USD
    order = Order(
        id=order_id,
        total_amount=Money(Decimal("500"), order_currecy)
    )
    payment = make_payment("450", order_id)
    payment.money = Money(Decimal("100"), payment_currency)
    payment._status = PaymentStatus.EXECUTED
    with pytest.raises(PaymentError) as e:
        order.refund_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Currency mismatch. Payment currency: `{payment_currency}`, "
        f"order currency: `{order_currecy}`."
    )


@pytest.mark.parametrize(
        "payment_status, message",
        [
            (PaymentStatus.CREATED, "Unacceptable payment status: `created`"),
            (PaymentStatus.PENDING, "Unacceptable payment status: `pending`"),
            (PaymentStatus.REJECTED, "Unacceptable payment status: `rejected`"),
            (PaymentStatus.CANCELLED, "Unacceptable payment status: `cancelled`"),
        ]
)
def test_accept_payment_with_non_executed_status_raises_error(
    order_id,
    payment_status,
    message
):
    total_amount=Money(Decimal("400"), Currency.RUB)
    order = Order(id=order_id, total_amount=total_amount)
    order._paid_amount = Money(Decimal("200"), Currency.RUB)

    payment = make_payment("100", order_id)
    payment._status = PaymentStatus.CREATED
    payment._is_accepted = True
    payment._status = payment_status

    with pytest.raises(PaymentError) as e:
        order.accept_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == message


@pytest.mark.parametrize(
        "payment_status, message",
        [
            (PaymentStatus.CREATED, "Unacceptable payment status: `created`"),
            (PaymentStatus.PENDING, "Unacceptable payment status: `pending`"),
            (PaymentStatus.REJECTED, "Unacceptable payment status: `rejected`"),
            (PaymentStatus.CANCELLED, "Unacceptable payment status: `cancelled`"),
        ]
)
def test_refund_payment_with_non_executed_status_raises_error(
    payment_status,
    message,
    order_id
):
    order = Order(
        id=order_id,
        total_amount=Money(Decimal("500"), Currency.RUB)
    )
    order._paid_amount = Money(Decimal("300"), Currency.RUB)
    payment = make_payment("100", order_id)
    payment._is_accepted = True
    payment._status = payment_status
    with pytest.raises(PaymentError) as e:
        order.refund_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == message


def test_accept_of_already_accepted_payment_raises_error(order_id):
    payment = make_payment("100", order_id)
    payment._status = PaymentStatus.EXECUTED
    payment._is_accepted = True
    total_amount=Money(Decimal("400"), Currency.RUB)
    order = Order(id=order_id, total_amount=total_amount)
    order._paid_amount = Money(Decimal("200"), Currency.RUB)
    with pytest.raises(PaymentError) as e:
        order.accept_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == "Payment has already been accepted"


def test_refund_of_already_refunded_payment_raises_error(order_id):
    payment = make_payment("100", order_id)
    payment._status = PaymentStatus.EXECUTED
    payment._is_refunded = True
    total_amount=Money(Decimal("400"), Currency.RUB)
    order = Order(id=order_id, total_amount=total_amount)
    order._paid_amount = Money(Decimal("200"), Currency.RUB)
    with pytest.raises(PaymentError) as e:
        order.refund_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == "Payment has already been refunded"

def test_refund_of_not_accepted_payment_raises_error(order_id):
    payment = make_payment("100", order_id)
    payment._status = PaymentStatus.EXECUTED
    total_amount=Money(Decimal("400"), Currency.RUB)
    order = Order(id=order_id, total_amount=total_amount)
    order._paid_amount = Money(Decimal("200"), Currency.RUB)
    with pytest.raises(PaymentError) as e:
        order.refund_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == "Payment has not been accepted"


def test_accept_payment_by_fully_paid_order_raises_error(order_id):
    order = Order(
        id=order_id,
        total_amount=Money(Decimal("500"), Currency.RUB)
    )
    order._paid_amount = order.total_amount
    payment = make_payment("100", order_id, Currency.RUB)
    payment._status = PaymentStatus.EXECUTED
    with pytest.raises(PaymentError) as e:
        order.accept_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == "Order is already paid"


def test_refund_payment_by_unpaid_order_raises_error(order_id):
    payment = make_payment("100", order_id)
    payment._status = PaymentStatus.EXECUTED
    payment._is_accepted = True
    total_amount=Money(Decimal("400"), Currency.RUB)
    order = Order(id=order_id, total_amount=total_amount)
    order._paid_amount = Money.zero(Currency.RUB)
    with pytest.raises(PaymentError) as e:
        order.refund_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == "Order is not paid"


def test_accept_payment_with_amount_exceeding_unpaid_amount_raises_error(order_id):
    payment = make_payment("450", order_id)
    payment._status = PaymentStatus.EXECUTED
    total_amount=Money(Decimal("500"), Currency.RUB)
    order = Order(id=order_id, total_amount=total_amount)
    order._paid_amount = Money(Decimal("400"), Currency.RUB)
    with pytest.raises(PaymentError) as e:
        order.accept_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Payment amount `{payment.money.amount}` "
        f"exceeds unpaid amount `{order.unpaid_amount.amount}`."
    )


def test_refund_payment_with_amount_exceeding_paid_amount_raises_error(order_id):
    payment = make_payment("450", order_id)
    payment._status = PaymentStatus.EXECUTED
    payment._is_accepted = True
    total_amount=Money(Decimal("400"), Currency.RUB)
    order = Order(id=order_id, total_amount=total_amount)
    order._paid_amount = Money(Decimal("200"), Currency.RUB)
    with pytest.raises(OrderError) as e:
        order.refund_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Amount to refund is: `{payment.money.amount}`. "
        f"This exceeds amount paid: `{order.paid_amount.amount}`"
    )
