from typing import (
    Optional,
    Any,
    Self,
)
from datetime import datetime



class FakeBaseRepo:
    def __init__(self, instances: list[Any]) -> None:
        self.instances = instances
        self.temp_added = []
        self.temp_deleted = []

    def add(self, instance) -> None:
        self.temp_added.append(instance)

    def get_by_db_id(self, instance_id) -> Optional[Any]:
        return next(
            (instance for instance in self.instances if instance.id == instance_id),
            None
        )

    def delete(self, instance) -> None:
        self.temp_deleted.append(instance)

    def execute_adding(self) -> None:
        for item in self.temp_added:
            if not item.id:
                item.id = 1
            if not item.created_at:
                item.created_at = datetime(1900, 1, 1)
            self.instances.append(item)
        self.temp_added = []

    def execute_deletion(self) -> None:
        for item in self.temp_deleted:
            self.instances.remove(item)
        self.temp_deleted = []


class FakePaymentsRepo(FakeBaseRepo):
    def __init__(self, model_cls: object, payments: list) -> None:
        self.model_cls = model_cls
        super().__init__(instances=payments)


class FakeOrdersRepo(FakeBaseRepo):
    def __init__(self, model_cls: object, orders: list) -> None:
        self.model_cls = model_cls
        super().__init__(instances=orders)


class FakeUnitOfWork:
    def __init__(self,
                 payments: FakePaymentsRepo,
                 orders: FakeOrdersRepo
    ) -> None:
        self.payments = payments
        self.orders = orders

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.rollback()

    def rollback(self) -> None:
        pass

    def commit(self) -> None:
        if self.payments and self.payments.temp_added:
            self.payments.execute_adding()
        if self.orders and self.orders.temp_added:
            self.orders.execute_adding()
        if self.payments and self.payments.temp_deleted:
            self.payments.execute_deletion()
        if self.orders and self.orders.temp_deleted:
            self.orders.execute_deletion()
