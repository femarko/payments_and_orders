from fastapi import Depends
from typing import Callable
from sqlalchemy import Engine
from payments.infrastructure.db.sqlalchemy_uow import SqlAlchemyUnitOfWork
from payments.infrastructure.db.sqlalchemy_session import (
    build_engine,
    session_factory,
    SessionFactory,
)
from payments.infrastructure.gateways.acquiring_gateway import BankGateway
from payments.application.use_cases import (
    DepositPayment,
    RefundPayment,
)
from payments.application.dto import MessageResponse
from payments.config import get_settings



def get_engine() -> Engine:
    return build_engine(get_settings().db_url)


def get_session_factory(engine: Engine = Depends(get_engine)) -> SessionFactory:
    return session_factory(engine)


def get_sa_uow(session_factory: SessionFactory = Depends(get_session_factory)) -> Callable[..., SqlAlchemyUnitOfWork]:
    return lambda: SqlAlchemyUnitOfWork(session_factory=session_factory)


def get_bank_gateway() -> BankGateway:
    return BankGateway(
        api_key=get_settings().bank_api_key,
        base_url=get_settings().bank_api_base_url
    )


def get_message_response() -> type[MessageResponse]:
    return MessageResponse


def get_deposit_payment_uc(
    uow: Callable[..., SqlAlchemyUnitOfWork] = Depends(get_sa_uow),
    bank_gateway: BankGateway = Depends(get_bank_gateway),
    response: type[MessageResponse] = Depends(get_message_response),
) -> DepositPayment:
    return DepositPayment(
        uow=uow,
        bank_gateway=bank_gateway,
        response=response
    )


def get_refund_payment_uc(
    uow: Callable[..., SqlAlchemyUnitOfWork] = Depends(get_sa_uow),
    bank_gateway: BankGateway = Depends(get_bank_gateway),
    response = Depends(get_message_response),
) -> RefundPayment:
    return RefundPayment(
        uow=uow,
        bank_gateway=bank_gateway,
        response=response
    )
