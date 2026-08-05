from decimal import Decimal

from payments.config import get_settings
from payments.domain.entities.payment import Payment
from payments.domain.entities.order import Order
from payments.domain.value_objects import (
    OrderId,
    Money,
)
from payments.domain.enums import (
    PaymentType,
    Currency,
)
from payments.infrastructure.db.sqlalchemy_repos import (
    PaymentRepo,
    OrderRepo
)
from payments.infrastructure.db.mappers import (
    order_to_model,
    order_to_entity,
    payment_to_entity,
    payment_to_model,
)
from payments.infrastructure.db.sqlalchemy_session import (
    session_factory,
    build_engine,
)



def test_payment_and_order_repos_successfully_add_and_get_by_id():
    db_url = get_settings().db_url
    engine = build_engine(db_url)
    start_session = session_factory(engine)
    session = start_session()
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
    order_repo= OrderRepo(
        session=session,
        to_model=order_to_model,
        to_entity=order_to_entity
    )
    payment_repo = PaymentRepo(
        session=session,
        to_model=payment_to_model,
        to_entity=payment_to_entity
    )
    try:
        order_repo.add(order)
        payment_repo.add(payment)
        session.flush()
        session.expire_all()
        assert order_repo.get_by_id(order.id) == order
        assert payment_repo.get_by_id(payment.id) == payment
    finally:
        session.rollback()
        session.close()
