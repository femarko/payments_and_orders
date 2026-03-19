import pytest
from decimal import Decimal

from tests.fakes.repos_and_uow import (
    FakeOrdersRepo,
    FakePaymentsRepo,
    FakeUnitOfWork,
)
from payments.application.use_cases import (
    PayOrder,
    RefundPayment,
)
from payments.application.dto import (
    MessageResponse,
    NewPaymentInput
)
from payments.domain.entities import (
    Payment,
    Order,
)
from payments.domain.value_objects import Money, OrderId
from payments.domain.enums import (
    Currency,
    OrderStatus,
    PaymentStatus,
    PaymentType
)



def test_pay_order_uc_execute_behaviour():
    order_id = OrderId.new()
    total_order_amount = Money(Decimal("100"), Currency.RUB)
    payment_amount = Money(Decimal("50"), Currency.RUB)
    order_to_pay = Order(id=order_id, total_amount=total_order_amount)
    fake_payments_repo = FakePaymentsRepo(model_cls=Payment, payments=[])
    fake_orders_repo = FakeOrdersRepo(model_cls=Order, orders=[order_to_pay])
    fake_uow = lambda: FakeUnitOfWork(fake_payments_repo, fake_orders_repo)
    pay_order_uc = PayOrder(uow=fake_uow, response=MessageResponse)
    payload = NewPaymentInput(
        order_id=order_id,
        payment_type=PaymentType.ACQUIRING,
        amount=str(payment_amount.amount),
        currency=Currency.RUB
    )
    order_to_pay_status_init = order_to_pay.status
    pay_order_uc.execute(payload)
    order_to_pay_status_new = order_to_pay.status
    assert order_to_pay_status_init == OrderStatus.UNPAID
    assert order_to_pay_status_new == OrderStatus.PARTIALLY_PAID
    assert fake_payments_repo.instances[0].status == PaymentStatus.DEPOSITED


def test_refund_payment_uc_execute_behaviour():
    order_id = OrderId.new()
    total_order_amount = Money(Decimal("100"), Currency.RUB)
    order = Order(id=order_id, total_amount=total_order_amount)
    order._paid_amount = total_order_amount
    order._status = OrderStatus.PAID
    payment = Payment.create(
        PaymentType.ACQUIRING,
        Money(Decimal("50"), Currency.RUB),
        order_id
    )
    payment._status = PaymentStatus.DEPOSITED
    fake_payments_repo = FakePaymentsRepo(model_cls=Payment, payments=[payment])
    fake_orders_repo = FakeOrdersRepo(model_cls=Order, orders=[order])
    fake_uow = lambda: FakeUnitOfWork(fake_payments_repo, fake_orders_repo)
    refund_payment_uc = RefundPayment(uow=fake_uow, response=MessageResponse)
    order_status_init = order.status
    payment_status_init = payment.status
    refund_payment_uc.execute(payment.id)
    order_status_new = order.status
    payment_status_new = payment.status
    assert order_status_init == OrderStatus.PAID
    assert order_status_new == OrderStatus.PARTIALLY_PAID
    assert payment_status_init == PaymentStatus.DEPOSITED
    assert payment_status_new == PaymentStatus.REFUNDED
