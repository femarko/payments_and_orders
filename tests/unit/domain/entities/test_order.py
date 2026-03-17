from typing import Callable

import pytest
from decimal import Decimal

from payments.domain.entities import (
    Payment,
    Order,
)
from payments.domain.enums import (
    PaymentStatus,
    OrderStatus,
)
from payments.domain.value_objects import (
    Money,
    OrderId,
)
from payments.domain.errors import PaymentError
from payments.domain.enums import (
    Currency,
    PaymentType
)



def make_payment(
        amount: str | int | Decimal,
        order_id: OrderId | Callable[..., OrderId],
        status=PaymentStatus.DEPOSITED
) -> Payment:
    payment = Payment.create(
        payment_type=PaymentType.ACQUIRING,
        money=Money(Decimal(amount)),
        order_id=order_id,
    )
    payment._status = status
    return payment


def make_order(
    order_id: OrderId,
    payments: list[Payment],
    total_amount: str | int | Decimal = "500",
    currency: Currency = Currency.RUB
) -> Order:
     return Order(
        id=order_id,
        total_amount=Money(Decimal(total_amount), currency),
        payments=payments,
    )


def test_paid_amount_returns_sum_of_successful_payments():
    payment_1 = make_payment("100", order_id)
    payment_2 = make_payment("200", order_id)
    order = make_order(order_id, [payment_1, payment_2])
    assert order.paid_amount == Money(Decimal("300"))


def test_unpaid_amount_property_subtracts_paid_amount_from_total_amount():
    payment = make_payment("300", order_id)
    order = make_order(order_id, [payment])
    assert order.unpaid_amount == Money(Decimal("200"))


@pytest.mark.parametrize(
        "total_order_amount, partially_paid_amount, expected",
        [
            ("200", "100", OrderStatus.PARTIALLY_PAID),
            # ("0", OrderStatus.UNPAID),
            # ("500", OrderStatus.PAID)
        ]
)
def test_update_order_status_sets_status_correctly(
    order_id,
    payment,
    total_order_amount,
    partially_paid_amount,
    expected
):
    order = make_order(
        order_id=order_id,
        total_amount=total_amount,
        payments=[make_payment(partially_paid_amount, order_id)]
)
    order.update_status()
    assert order.status == expected


def test_add_payment(order_id):
    payment_1 = make_payment("100", order_id)
    payment_2 = make_payment("200", order_id)
    order = make_order(order_id, [payment_1])
    order.add_payment(payment_2)
    assert order.payments == [payment_1, payment_2]


def test_adding_final_payment_sets_order_status_to_paid():
    payment_1 = make_payment("100", order_id)
    payment_2 = make_payment("400", order_id)
    order = make_order(order_id, payments=[payment_1])
    order.add_payment(payment_2)
    assert order.status == OrderStatus.PAID


def test_adding_extra_payment_raises_error():
    payment_1 = make_payment("450", order_id)
    payment_2 = make_payment("100", order_id)
    order = make_order(order_id, payments=[payment_1])
    with pytest.raises(PaymentError):
        order.add_payment(payment_2)


def test_adding_payment_to_paid_order_raises_error():
    payment_1 = make_payment("500", order_id)
    payment_2 = make_payment("10", order_id)
    order = make_order(order_id, payments=[payment_1])
    order.update_status()
    with pytest.raises(PaymentError):
        order.add_payment(payment_2)


def test_refund_sets_order_status_to_refunded(order_id):
    payment_1 = make_payment("300", order_id)
    payment_2 = make_payment("200", order_id)
    order = make_order(order_id, payments=[payment_1, payment_2])
    order.refund_payment(payment_2.id)
    assert order.payments[1].status == PaymentStatus.REFUNDED
