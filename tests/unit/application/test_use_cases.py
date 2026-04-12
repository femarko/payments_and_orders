import pytest
from dataclasses import dataclass
from datetime import (
    datetime,
    timezone,
)
from decimal import Decimal
from types import NoneType

from tests.fakes.repos_and_uow import (
    FakeOrdersRepo,
    FakePaymentsRepo,
    FakeUnitOfWork,
)
from payments.application.use_cases import (
    DepositPayment,
    RefundPayment,
    BaseUseCase,
)
from payments.application.dto import (
    MessageResponse,
    PaymentParams
)
from payments.domain.entities.payment import Payment
from payments.domain.entities.order import Order
from payments.domain.value_objects import (
    Money,
    OrderId,
    PaymentId
)
from payments.domain.enums import (
    Currency,
    OrderStatus,
    PaymentStatus,
    PaymentType
)
from payments.application.interfaces\
.acquiring_gateway_interface import CheckBankStatusResult
from payments.domain.errors import (
    PaymentError,
    NotFoundError,
    BankError,
    ErrorCode,
)


class FakeBankGateway:
    def __init__(self, api_key: str, start_url: str, check_url: str) -> None:
        pass

    def start_acquiring(self, payment: Payment) -> CheckBankStatusResult:
        return CheckBankStatusResult(
            status=PaymentStatus.PENDING,
            error=None
        )

    def check_payment(self, payment: Payment) -> CheckBankStatusResult:
        return CheckBankStatusResult(
            status=PaymentStatus.EXECUTED,
            error=None
        )


def test_deposit_payment_uc_behaviour():
    
    order_id = OrderId.new()
    total_order_amount = Money(Decimal("100"), Currency.RUB)
    order = Order(id=order_id, total_amount=total_order_amount)

    order_before = (order.status, isinstance(order.updated_at, NoneType))
    
    fake_orders_repo = FakeOrdersRepo(entity_cls=Order, orders=[order])
    payment_amount = Money(Decimal("50"), Currency.RUB)
    payment = Payment.create(PaymentType.ACQUIRING, payment_amount, order_id)
    
    payment_before = (
        payment._is_accepted,
        isinstance(payment._accepted_at, NoneType)
    )

    fake_payments_repo = FakePaymentsRepo(Payment, [payment])
    fake_uow = lambda: FakeUnitOfWork(fake_payments_repo, fake_orders_repo)
    fake_bank_gateway = FakeBankGateway(
        "test",
        "https://bank.api/acquiring_start",
        "https://bank.api/acquiring_check"
    )
    deposit_payment_uc = DepositPayment(
        uow=fake_uow,
        bank_gateway=fake_bank_gateway,
        response=MessageResponse
    )
    payload = PaymentParams(
        id=payment.id,
        order_id=order_id,
        payment_type=PaymentType.ACQUIRING,
        amount=str(payment_amount.amount),
        currency=Currency.RUB
    )

    uc_response = deposit_payment_uc.execute(payload)
    
    order_after = (
        order.status,
        isinstance(order.updated_at, datetime)
    )
    payment_after = (
        payment._is_accepted,
        isinstance(payment._accepted_at, datetime)
    )

    assert order_before == (OrderStatus.UNPAID, True)
    assert order_after == (OrderStatus.PARTIALLY_PAID, True)
    assert payment_before == (False, True)
    assert payment_after == (True, True)
    assert uc_response.message == f"Payment accepted at {payment.accepted_at}"


def test_refund_payment_uc_behaviour():
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
    payment._mark_as_accepted(datetime.now(timezone.utc))
    fake_payments_repo = FakePaymentsRepo(entity_cls=Payment, payments=[payment])
    fake_orders_repo = FakeOrdersRepo(entity_cls=Order, orders=[order])
    fake_uow = lambda: FakeUnitOfWork(fake_payments_repo, fake_orders_repo)
    fake_bank_gateway = FakeBankGateway(
        "test",
        "https://bank.api/acquiring_start",
        "https://bank.api/acquiring_check"
    )
    refund_payment_uc = RefundPayment(
        uow=fake_uow,
        bank_gateway=fake_bank_gateway,
        response=MessageResponse
    )
    order_status_init = order.status
    payment_status_init = payment.status

    uc_response = refund_payment_uc.execute(payment.id)

    order_status_new = order.status
    payment_status_new = payment.status

    assert order_status_init == OrderStatus.PAID
    assert order_status_new == OrderStatus.PARTIALLY_PAID
    assert payment_status_init == PaymentStatus.CREATED
    assert payment_status_new == PaymentStatus.EXECUTED
    assert uc_response.message == f"Success"


def test_base_uc_fetch_from_db_not_found_scenario():
    fake_payments_repo = FakePaymentsRepo(entity_cls=Payment, payments=[])
    fake_orders_repo = FakeOrdersRepo(entity_cls=Order, orders=[])
    fake_uow = lambda: FakeUnitOfWork(fake_payments_repo, fake_orders_repo)
    fake_bank_gateway = FakeBankGateway(
        "test",
        "https://bank.api/acquiring_start",
        "https://bank.api/acquiring_check"
    )
    base_uc = BaseUseCase(
        uow=fake_uow,
        bank_gateway=fake_bank_gateway,
        response=MessageResponse
    )
    id=PaymentId.new()

    with pytest.raises(NotFoundError) as e:
        base_uc._fetch_from_db(fake_orders_repo, id)
    assert e.value.code == ErrorCode.NOT_FOUND
    assert e.value.message == f"Object with id={str(id)} is not found"


def test_check_bank_status_raises_error_with_non_bank_payment():
    fake_payments_repo = FakePaymentsRepo(entity_cls=Payment, payments=[])
    fake_orders_repo = FakeOrdersRepo(entity_cls=Order, orders=[])
    fake_uow = lambda: FakeUnitOfWork(fake_payments_repo, fake_orders_repo)
    fake_bank_gateway = FakeBankGateway(
        "test",
        "https://bank.api/acquiring_start",
        "https://bank.api/acquiring_check"
    )
    base_uc = BaseUseCase(
        uow=fake_uow,
        bank_gateway=fake_bank_gateway,
        response=MessageResponse
    )
    payment = Payment.create(
        PaymentType.CASH,
        Money(Decimal("50"), Currency.RUB),
        order_id=OrderId.new()
    )

    with pytest.raises(PaymentError) as e:
        base_uc._check_bank_status(payment)
    assert e.value.code == ErrorCode.FORBIDDEN_OPERATION
    assert e.value.message == f"Non-acquiring payment: {payment.type = }"


def test_check_bank_status_raises_error_when_banK_returns_error():
    fake_payments_repo = FakePaymentsRepo(entity_cls=Payment, payments=[])
    fake_orders_repo = FakeOrdersRepo(entity_cls=Order, orders=[])
    fake_uow = lambda: FakeUnitOfWork(fake_payments_repo, fake_orders_repo)
    
    @dataclass
    class FakeBankGatewayReturningError:
        def check_payment(self, payment: Payment) -> CheckBankStatusResult:
            return CheckBankStatusResult(status=None, error="Bank error")

    base_uc = BaseUseCase(
        uow=fake_uow,
        bank_gateway=FakeBankGatewayReturningError(),
        response=MessageResponse
    )
    payment = Payment.create(
        PaymentType.ACQUIRING,
        Money(Decimal("50"), Currency.RUB),
        order_id=OrderId.new()
    )
    with pytest.raises(BankError) as e:
        base_uc._check_bank_status(payment)
    assert e.value.code == ErrorCode.EXTERNAL_API_ERROR
    assert e.value.message == "Failed to update payment external status"


def test_check_bank_status_raises_error_when_bank_does_not_return_status():
    fake_payments_repo = FakePaymentsRepo(entity_cls=Payment, payments=[])
    fake_orders_repo = FakeOrdersRepo(entity_cls=Order, orders=[])
    fake_uow = lambda: FakeUnitOfWork(fake_payments_repo, fake_orders_repo)
    
    @dataclass
    class FakeBankGatewayReturningNoneStatus:
        def check_payment(self, payment: Payment) -> CheckBankStatusResult:
            return CheckBankStatusResult(status=None, error=None)

    base_uc = BaseUseCase(
        uow=fake_uow,
        bank_gateway=FakeBankGatewayReturningNoneStatus(),
        response=MessageResponse
    )
    payment = Payment.create(
        PaymentType.ACQUIRING,
        Money(Decimal("50"), Currency.RUB),
        order_id=OrderId.new()
    )
    with pytest.raises(BankError) as e:
        base_uc._check_bank_status(payment)
    assert e.value.code == ErrorCode.EXTERNAL_API_ERROR
    assert e.value.message == "Failed to update payment external status"
    

def test_early_return_when_payment_is_already_accepted():
    payment = Payment.create(
        PaymentType.ACQUIRING,
        Money(Decimal("50"), Currency.RUB),
        order_id=OrderId.new()
    )
    fake_payments_repo = FakePaymentsRepo(entity_cls=Payment, payments=[payment])
    fake_orders_repo = FakeOrdersRepo(entity_cls=Order, orders=[])
    fake_uow = lambda: FakeUnitOfWork(fake_payments_repo, fake_orders_repo)
    fake_bank_gateway = FakeBankGateway(
        "test",
        "https://bank.api/acquiring_start",
        "https://bank.api/acquiring_check"
    )
    deposit_payment_uc = DepositPayment(
        uow=fake_uow,
        bank_gateway=fake_bank_gateway,
        response=MessageResponse
    )
    payload = PaymentParams(
        id=payment.id,
        order_id=payment.order_id,
        payment_type=payment.type,
        amount=str(payment.money.amount),
        currency=payment.money.currency
    )
    accepted_at = datetime.now(timezone.utc)
    payment._mark_as_accepted(accepted_at)
    uc_response = deposit_payment_uc.execute(payload)
    assert uc_response.message == f"Already accepted at {accepted_at}"


def test_early_return_when_payment_is_already_refunded():
    payment = Payment.create(
        PaymentType.ACQUIRING,
        Money(Decimal("50"), Currency.RUB),
        order_id=OrderId.new()
    )
    fake_payments_repo = FakePaymentsRepo(entity_cls=Payment, payments=[payment])
    fake_orders_repo = FakeOrdersRepo(entity_cls=Order, orders=[])
    fake_uow = lambda: FakeUnitOfWork(fake_payments_repo, fake_orders_repo)
    fake_bank_gateway = FakeBankGateway(
        "test",
        "https://bank.api/acquiring_start",
        "https://bank.api/acquiring_check"
    )
    refund_payment_uc = RefundPayment(
        uow=fake_uow,
        bank_gateway=fake_bank_gateway,
        response=MessageResponse
    )
    accepted_at = datetime.now(timezone.utc)
    payment._mark_as_refunded(accepted_at)
    uc_response = refund_payment_uc.execute(payment.id)
    assert uc_response.message == f"Already refunded at {accepted_at}"
