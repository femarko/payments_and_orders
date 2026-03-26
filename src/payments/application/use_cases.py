from decimal import Decimal
from typing import (
    Callable,
    Generic,
)
from payments.application.interfaces.uow_interface import UoWProto
from payments.domain.entities.payment import Payment
from payments.domain.entities.order import Order

from payments.domain.repos_interfaces import (
    RepoProto,
)
from payments.domain.value_objects import (
    OrderId,
    PaymentId,
    Money,
)
from payments.domain.errors import NotFoundError
from payments.domain.enums import (
    PaymentType,
    PaymentStatus,
)
from payments.application.dto import (
    TResponse,
    PaymentParams,
    MessageResponse
)
from payments.application.interfaces.acquiring_gateway_interface import (
    BankGatewayProto,
    CheckBankStatusResult,
)
from payments.domain.errors import (
    ErrorCode,
    BankError,
    PaymentError,
)


class BaseUseCase(Generic[TResponse]):
    def __init__(
            self,
            uow: Callable[..., UoWProto],
            bank_gateway: BankGatewayProto,
            response: type[TResponse]
     ) -> None:
        self.uow = uow
        self.response = response
        self.bank_gateway = bank_gateway

    def _fetch_from_db(
            self,
            repo: RepoProto,
            id: OrderId | PaymentId,
        ) :
        result = repo.get_by_id(id)
        if not result:
            raise NotFoundError(f"Object with {id=} is not found")
        return result

    def _check_bank_status(self, payment: Payment) -> CheckBankStatusResult:
        if not payment.type == PaymentType.ACQUIRING:
            code = ErrorCode.FORBIDDEN_OPERATION
            message = f"Non-acquiring payment: {payment.type = }"
            raise PaymentError(code, message)
        bank_result = self.bank_gateway.check_payment(payment)
        if bank_result.error:
            code = ErrorCode.EXTERNAL_API_ERROR
            message ="Failed to update payment external status"
            raise BankError(code, message)
        if not bank_result.status:
            raise PaymentError(
                ErrorCode.EXTERNAL_API_ERROR,
                "Failed to update payment external status"
            )
        return bank_result

    def _create_payment(
            self,
            uow: UoWProto,
            payload: PaymentParams
        ) -> Payment:
        payment = Payment.create(
            payment_type=payload.payment_type,
            money=Money(
                amount=Decimal(payload.amount),
                currency=payload.currency,
            ),
            order_id=payload.order_id
        )
        return payment
    

class DepositPayment(BaseUseCase[MessageResponse]):
    def execute(self, payload: PaymentParams) -> MessageResponse:
        with self.uow() as uow:
            payment: Payment = self._fetch_from_db(uow.payments, payload.id)
            if payment.is_accepted:
                return self.response(
                    message=f"Already accepted at {payment.accepted_at}"
                )
            if payment.type == PaymentType.ACQUIRING:
                bank_result = self._check_bank_status(payment)
                payment.update_bank_status(status=bank_result.status)
            order: Order = self._fetch_from_db(uow.orders, payload.order_id)
            order.accept_payment(payment)
            uow.commit()
            acceptance_time = payment.accepted_at
        return self.response(
            message=f"Payment accepted at {acceptance_time}"
        )


class RefundPayment(BaseUseCase[MessageResponse]):
    def execute(self, payment_id: PaymentId) -> MessageResponse:
        with self.uow() as uow:
            payment: Payment = self._fetch_from_db(uow.payments, payment_id)    
            if payment.type == PaymentType.ACQUIRING:
                bank_result = self._check_bank_status(payment)
                payment.update_bank_status(status=bank_result.status)
            order_id = payment.order_id
            order: Order = self._fetch_from_db(uow.orders, order_id)
            order.refund_payment(payment)
            uow.commit()
        return self.response(message="Success")
