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
    def add(self, instance: T_Domain_Entity) -> None: ...
    def get_by_id(self, instance_id: T_Domain_ID) -> Optional[T_Domain_Entity]: ...
    def delete(self, instance: T_Domain_Entity) -> None: ...


class OrderRepoProto(RepoProto[Order, OrderId]): ...


class PaymentRepoProto(RepoProto[Payment, PaymentId]): ...
