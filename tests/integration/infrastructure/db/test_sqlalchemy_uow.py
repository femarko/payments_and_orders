from decimal import Decimal

from payments.domain.value_objects import (
    OrderId,
    Money,
    Currency,
)
from payments.domain.entities.payment import Payment
from payments.domain.entities.order import Order
from payments.domain.enums import (
    PaymentType
)
from payments.infrastructure.db.sqlalchemy_uow import SqlAlchemyUnitOfWork
from payments.infrastructure.db.sqlalchemy_session import (
    session_factory,
    build_engine,
    build_db_url,
)



def test_sqlalchemy_uow_adds_and_commits() -> None:
    from payments.env import init_env
    init_env(use_load_dotenv=True, env_file=".env.example")
    from payments.config import Settings
    db_url = build_db_url(Settings)
    engine = build_engine(db_url)
    start_session = session_factory(engine)
    order_id = OrderId.new()
    order = Order(
        id=order_id,
        total_amount=Money(Decimal("100"), Currency.RUB)
    )
    payment = Payment.create(
        order_id=order_id,
        payment_type=PaymentType.ACQUIRING,
        money=Money(Decimal("100"), Currency.RUB),
    )
    payment_id = payment.id
    with SqlAlchemyUnitOfWork(session_factory=start_session) as uow:
        uow.orders.add(order)
        uow.payments.add(payment)
        uow.commit()
    with SqlAlchemyUnitOfWork(session_factory=start_session) as uow:
        order_fetched = uow.orders.get_by_id(order_id)
        payment_fetched = uow.payments.get_by_id(payment_id)
    assert order_fetched == order
    assert payment_fetched == payment


def test_uow_rolls_back_on_error() -> None:
    from payments.env import init_env
    init_env(use_load_dotenv=True, env_file=".env.example")
    from payments.config import Settings
    db_url = build_db_url(Settings)
    engine = build_engine(db_url)
    start_session = session_factory(engine)
    order = Order(
        id=OrderId.new(),
        total_amount=Money(Decimal("100"), Currency.RUB)
    )
    payment = Payment.create(
        order_id=order.id,
        payment_type=PaymentType.ACQUIRING,
        money=Money(Decimal("100"), Currency.RUB),
    )
    try:
        with SqlAlchemyUnitOfWork(session_factory=start_session) as uow:
            uow.orders.add(order)
            uow.payments.add(payment)
            raise Exception("error")
    except Exception:
        pass

    with SqlAlchemyUnitOfWork(session_factory=start_session) as uow:
        order_fetched = uow.orders.get_by_id(order.id)
        payment_fetched = uow.payments.get_by_id(payment.id)
    assert order_fetched is None
    assert payment_fetched is None
