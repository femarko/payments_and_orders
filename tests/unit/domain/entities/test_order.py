import pytest
from decimal import Decimal
from types import NoneType
from datetime import datetime

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


def test_accept_payment_changes_order_and_payment_state():

    order = Order(
        money=Money(Decimal("500"), Currency.RUB)
    )
    order_state_before = order.params()
    
    payment = make_payment(amount="300", order_id=order.id)
    payment._status = PaymentStatus.EXECUTED
    payment_state_before = payment.params()
    
    order.accept_payment(payment)
    
    order_state_after = order.params()
    payment_state_after = payment.params()
        
    assert order_state_before["status"] == OrderStatus.UNPAID
    assert order_state_before["unpaid_amount"] == Money(Decimal("500"), Currency.RUB)
    assert order_state_before["paid_amount"] == Money.zero(Currency.RUB)
    assert isinstance(order_state_before["updated_at"], NoneType)
    assert order_state_after["status"] == OrderStatus.PARTIALLY_PAID
    assert order_state_after["unpaid_amount"] == Money(Decimal("200"), Currency.RUB)
    assert order_state_after["paid_amount"] == Money(Decimal("300"), Currency.RUB)
    assert isinstance(order_state_after["updated_at"], datetime)

    assert payment_state_before["is_accepted"] == False
    assert isinstance(payment_state_before["updated_at"], NoneType)
    assert payment_state_after["is_accepted"] == True
    assert isinstance(payment_state_after["updated_at"], datetime)


def test_refund_payment_changes_order_and_payment_state():
    total_amount = Money(Decimal("500"), Currency.RUB)
    order = Order(money=total_amount)
    order._paid_amount = total_amount
    order_before = order.params()
    payment = make_payment("300", order.id)
    payment._is_accepted = True
    payment._status = PaymentStatus.EXECUTED
    payment_before = payment.params()
    order.refund_payment(payment)
    order_after = order.params()
    payment_after = payment.params()
    assert order_before["id"] == order_after["id"]
    assert all((
        order_before["total_amount"] == Money(Decimal("500"), Currency.RUB),
        order_after["total_amount"] == Money(Decimal("500"), Currency.RUB),
    ))
    assert all((
        order_before["paid_amount"] == Money(Decimal("500"), Currency.RUB),
        order_after["paid_amount"] == Money(Decimal("200"), Currency.RUB),
        ))
    assert all((
        order_before["unpaid_amount"] == Money.zero(Currency.RUB),
        order_after["unpaid_amount"] == Money(Decimal("300"), Currency.RUB),
    ))
    assert all((
        isinstance(order_before["created_at"], datetime),
        order_after["created_at"] == order_before["created_at"],
    ))
    assert all((
        order_before["updated_at"] is None,
        isinstance(order_after["updated_at"], datetime),
    ))
    assert all((
        order_before["status"] == OrderStatus.PAID,
        order_after["status"] == OrderStatus.PARTIALLY_PAID,
    ))
    assert payment_before["id"] == payment_after["id"]
    assert payment_before["type"] == payment_before["type"] == \
        PaymentType.ACQUIRING
    assert all((
        payment_before["status"] == PaymentStatus.EXECUTED,
        payment_after["status"] == PaymentStatus.EXECUTED,
    ))
    assert all((
        payment_before["money"] == Money(Decimal("300"), Currency.RUB),
        payment_after["money"] == Money(Decimal("300"), Currency.RUB),
    ))
    assert payment_before["order_id"] == payment_after["order_id"] == order.id
    assert all((
        isinstance(payment_before["created_at"], datetime),
        payment_after["created_at"] == payment_before["created_at"],
    ))
    assert all((
        payment_before["updated_at"] is None,
        isinstance(payment_after["updated_at"], datetime),
    ))
    assert payment_before["external_id"] == payment_after["external_id"] == None
    assert all((
        payment_before["is_accepted"] == True,
        payment_after["is_accepted"] == False,
    ))


def test_unpaid_amount_property_subtracts_paid_amount_from_total_amount():
    order = Order(money=Money(Decimal("100"), Currency.RUB))
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
    paid_amount,
    expected
):
    order = Order(money=Money(Decimal("100"), Currency.RUB))
    order._paid_amount = Money(Decimal(paid_amount), Currency.RUB)
    assert order.status == expected


def test_order_status_cannot_be_set_manually():
    order = Order(money=Money(Decimal("100"), Currency.RUB))
    with pytest.raises(DomainAttributeError) as e:
        order.status = OrderStatus.PAID
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Direct modification of this attribute "
        f"is forbidden. Use domain methods instead."
        f" Domain methods: `accept_payment`, `refund_payment`."
    )


def test_order_paid_amount_cannot_be_set_manually():
    order = Order(money=Money(Decimal("100"), Currency.RUB))
    with pytest.raises(DomainAttributeError) as e:
        order.paid_amount = Money(Decimal("50"), Currency.RUB)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Direct modification of this attribute "
        f"is forbidden. Use domain methods instead."
        f" Domain methods: `accept_payment`, `refund_payment`."
    )


def test_order_unpaid_amount_cannot_be_set_manually():
    order = Order(money=Money(Decimal("100"), Currency.RUB))
    with pytest.raises(DomainAttributeError) as e:
        order.unpaid_amount = Money(Decimal("50"), Currency.RUB)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Direct modification of this attribute "
        f"is forbidden. Use domain methods instead."
        f" Domain methods: `accept_payment`, `refund_payment`."
    )


def test_accept_payment_with_wrong_order_id_raises_error():
    wrong_order_id = OrderId.new()
    payment = make_payment("450", wrong_order_id)
    payment._status = PaymentStatus.EXECUTED
    total_amount=Money(Decimal("400"), Currency.RUB)
    order = Order(money=total_amount)
    with pytest.raises(PaymentError) as e:
        order.accept_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message ==  (
        f"Incorrect order ID in payment credentials "
        f"order: id={order.id}, payment: order_id={wrong_order_id}"
    )


def test_refund_payment_with_wrong_order_id_raises_error():
    wrong_order_id = OrderId.new()
    payment = make_payment("450", wrong_order_id)
    payment._status = PaymentStatus.EXECUTED
    total_amount=Money(Decimal("400"), Currency.RUB)
    order = Order(money=total_amount)
    with pytest.raises(PaymentError) as e:
        order.refund_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Incorrect order ID in payment credentials "
        f"order: id={order.id}, payment: order_id={wrong_order_id}"
    )


def test_accept_payment_with_wrong_currency_raises_error():
    order_currecy = Currency.RUB
    payment_currency = Currency.USD
    order = Order(money=Money(Decimal("500"), order_currecy))
    payment = make_payment("450", order.id)
    payment.money = Money(Decimal("100"), payment_currency)
    payment._status = PaymentStatus.EXECUTED
    with pytest.raises(PaymentError) as e:
        order.accept_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Currency mismatch. Payment currency: `{payment_currency}`, "
        f"order currency: `{order_currecy}`."
    )


def test_refund_payment_with_wrong_currency_raises_error():
    order_currecy = Currency.RUB
    payment_currency = Currency.USD
    order = Order(money=Money(Decimal("500"), order_currecy))
    payment = make_payment("450", order.id)
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
    payment_status,
    message
):
    total_amount=Money(Decimal("400"), Currency.RUB)
    order = Order(money=total_amount)
    order._paid_amount = Money(Decimal("200"), Currency.RUB)

    payment = make_payment("100", order.id)
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
):
    order = Order(money=Money(Decimal("500"), Currency.RUB))
    order._paid_amount = Money(Decimal("300"), Currency.RUB)
    payment = make_payment("100", order.id)
    payment._is_accepted = True
    payment._status = payment_status
    with pytest.raises(PaymentError) as e:
        order.refund_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == message


def test_accept_of_already_accepted_payment_raises_error():
    total_amount=Money(Decimal("400"), Currency.RUB)
    order = Order(money=total_amount)
    payment = make_payment("100", order.id)
    payment._status = PaymentStatus.EXECUTED
    payment._is_accepted = True
    order._paid_amount = Money(Decimal("200"), Currency.RUB)
    with pytest.raises(PaymentError) as e:
        order.accept_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == "Payment has already been accepted"


def test_refund_of_already_refunded_payment_raises_error():
    total_amount=Money(Decimal("400"), Currency.RUB)
    order = Order(money=total_amount)
    payment = make_payment("100", order.id)
    payment._status = PaymentStatus.EXECUTED
    payment._is_accepted = False
    order._paid_amount = Money(Decimal("200"), Currency.RUB)
    with pytest.raises(PaymentError) as e:
        order.refund_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == "Payment has not been accepted"

def test_refund_of_not_accepted_payment_raises_error():
    total_amount=Money(Decimal("400"), Currency.RUB)
    order = Order(money=total_amount)
    payment = make_payment("100", order.id)
    payment._status = PaymentStatus.EXECUTED

    order._paid_amount = Money(Decimal("200"), Currency.RUB)
    with pytest.raises(PaymentError) as e:
        order.refund_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == "Payment has not been accepted"


def test_accept_payment_by_fully_paid_order_raises_error():
    order = Order(money=Money(Decimal("500"), Currency.RUB))
    order._paid_amount = order.total_amount
    payment = make_payment("100", order.id, Currency.RUB)
    payment._status = PaymentStatus.EXECUTED
    with pytest.raises(PaymentError) as e:
        order.accept_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == "Order is already paid"


def test_refund_payment_by_unpaid_order_raises_error():
    total_amount=Money(Decimal("400"), Currency.RUB)
    order = Order(money=total_amount)
    payment = make_payment("100", order.id)
    payment._status = PaymentStatus.EXECUTED
    payment._is_accepted = True
    order._paid_amount = Money.zero(Currency.RUB)
    with pytest.raises(PaymentError) as e:
        order.refund_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == "Order is not paid"


def test_accept_payment_with_amount_exceeding_unpaid_amount_raises_error():
    total_amount=Money(Decimal("500"), Currency.RUB)
    order = Order(money=total_amount)
    payment = make_payment("450", order.id)
    payment._status = PaymentStatus.EXECUTED
    order._paid_amount = Money(Decimal("400"), Currency.RUB)
    with pytest.raises(PaymentError) as e:
        order.accept_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Payment amount `{payment.money.amount}` "
        f"exceeds unpaid amount `{order.unpaid_amount.amount}`."
    )


def test_refund_payment_with_amount_exceeding_paid_amount_raises_error():
    total_amount=Money(Decimal("400"), Currency.RUB)
    order = Order(money=total_amount)
    payment = make_payment("450", order.id)
    payment._status = PaymentStatus.EXECUTED
    payment._is_accepted = True
    order._paid_amount = Money(Decimal("200"), Currency.RUB)
    with pytest.raises(OrderError) as e:
        order.refund_payment(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == (
        f"Amount to refund is: `{payment.money.amount}`. "
        f"This exceeds amount paid: `{order.paid_amount.amount}`"
    )
