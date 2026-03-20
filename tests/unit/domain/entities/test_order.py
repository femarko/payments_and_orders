import pytest
from decimal import Decimal
from typing import Callable
from datetime import (
    datetime,
    timezone
)

from payments.domain.entities import (
    Payment,
    Order,
)
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
    OrderError,
    ErrorCode,
    PaymentError
)
from payments.domain.enums import (
    Currency,
    PaymentType
)



@pytest.fixture
def order_id():
     return OrderId.new()


def make_payment(
        amount: str | int | Decimal,
        order_id: OrderId
) -> Payment:
    payment = Payment.create(
        payment_type=PaymentType.ACQUIRING,
        money=Money(Decimal(amount), Currency.RUB),
        order_id=order_id,
    )
    return payment


def test_accept_payment_changes_order_state(order_id):

    order = Order(id=order_id, total_amount=Money(Decimal("500"), Currency.RUB))
    
    updated_at_before = order.updated_at
    state_before = (order.status, order.unpaid_amount, order.paid_amount, type(updated_at_before))
    
    payment = make_payment(amount="300", order_id=order_id)
    order.accept_payment(payment.money)
    
    updated_at_after = order.updated_at
    state_after = (order.status, order.unpaid_amount, order.paid_amount, type(updated_at_after))

    assert state_before == (
        OrderStatus.UNPAID,
        Money(Decimal("500"), Currency.RUB),
        Money.zero(Currency.RUB),
        type(None)
    )
    assert state_after == (
        OrderStatus.PARTIALLY_PAID,
        Money(Decimal("200"), Currency.RUB),
        Money(Decimal("300"), Currency.RUB),
        type(datetime.now(timezone.utc))
    )


def test_refund_changes_order_state(order_id):
    total_amount = Money(Decimal("500"), Currency.RUB)
    order = Order(id=order_id, total_amount=total_amount)
    order._paid_amount = total_amount
    order._status = OrderStatus.PAID
    
    updated_at_before = order.updated_at
    state_before = (order.status, order.unpaid_amount, order.paid_amount, type(updated_at_before))
    
    payment = make_payment("300", order_id)
    order.refund_payment(payment.money)
    
    updated_at_after = order.updated_at
    state_after = (order.status, order.unpaid_amount, order.paid_amount, type(updated_at_after))

    assert state_before == (
        OrderStatus.PAID,
        Money.zero(Currency.RUB),
        Money(Decimal("500"), Currency.RUB),
        type(None)
    )
    assert state_after == (
        OrderStatus.PARTIALLY_PAID,
        Money(Decimal("300"), Currency.RUB),
        Money(Decimal("200"), Currency.RUB),
        type(datetime.now(timezone.utc))
    )


def test_unpaid_amount_property_subtracts_paid_amount_from_total_amount(order_id):
    order = Order(id = order_id, total_amount=Money(Decimal("100"), Currency.RUB))
    order._paid_amount = Money(Decimal("30"), Currency.RUB)
    assert order.unpaid_amount == Money(Decimal("70"), Currency.RUB)


@pytest.mark.parametrize(
        "payment_amount, expected",
        [
            ("100", OrderStatus.PARTIALLY_PAID),
            ("0", OrderStatus.UNPAID),
            ("500", OrderStatus.PAID)
        ]
)
def test_update_order_status_sets_status_correctly(payment_amount, expected):
    payment = make_payment(payment_amount, order_id)
    order = Order(id=order_id, total_amount=Money(Decimal("500"), Currency.RUB))
    order.accept_payment(payment.money)
    assert order.status == expected


def test_adding_extra_payment_raises_error(order_id):
    payment = make_payment("450", order_id)
    total_amount=Money(Decimal("400"), Currency.RUB)
    order = Order(id=order_id, total_amount=total_amount)
    order._paid_amount = total_amount
    with pytest.raises(PaymentError, match="Order is already paid") as e:
        order.accept_payment(payment.money)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
