from typing import Self

from payments.infrastructure.db.sqlalchemy_repos import (
    OrderRepo,
    PaymentRepo,
)
from payments.infrastructure.db.mappers import (
    order_to_entity,
    order_to_model,
    payment_to_entity,
    payment_to_model,
)



class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> Self:
        self.session = self._session_factory()
        self.payments = PaymentRepo(
            session=self.session,
            to_model=payment_to_model,
            to_entity=payment_to_entity
        )
        self.orders = OrderRepo(
            session=self.session,
            to_model=order_to_model,
            to_entity=order_to_entity
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        try:
            if exc_type:
                self.rollback()
        finally:
            self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
