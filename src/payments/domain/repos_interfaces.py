from typing import(
    Protocol,
    Optional
)

from payments.domain.entities import T_Domain_Entity
from payments.domain.entities.order import Order
from payments.domain.entities.payment import Payment
from payments.domain.value_objects import(
    OrderId,
    PaymentId,
    T_Domain_ID,
)



class RepoProto(Protocol[T_Domain_Entity, T_Domain_ID]):
    entity_cls: type[T_Domain_Entity]

    def entity_to_model(self, orm_model: object) -> object: ...
    def model_to_entity(self, orm_model: object) -> T_Domain_Entity: ...
    def add(self, instance: T_Domain_Entity) -> None: ...
    def get_by_id(self, instance_id: T_Domain_ID) -> Optional[T_Domain_Entity]: ...
    def delete(self, instance: T_Domain_Entity) -> None: ...
    def query(self) -> list[T_Domain_Entity]: ...


class OrderRepoProto(RepoProto[Order, OrderId]): ...


class PaymentRepoProto(RepoProto[Payment, PaymentId]): ...
