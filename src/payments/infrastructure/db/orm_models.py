from sqlalchemy.orm import (
    DeclarativeBase,
    relationship,
)
from sqlalchemy import (
    Column,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID as sqlalch_uuid
from typing import TypeVar
from payments.domain.value_objects import MoneyConfig


class SQLAlchBaseModel(DeclarativeBase): ...


T_SQLAlchBaseModel = TypeVar("T_SQLAlchBaseModel", bound=type[SQLAlchBaseModel])


class SQLAlchPaymentModel(SQLAlchBaseModel):
    __tablename__ = "payments"
    id = Column(sqlalch_uuid(as_uuid=True), primary_key=True, index=True)
    type = Column(String, index=True, nullable=False)
    status = Column(String, index=True, nullable=False)
    amount = Column(
        Numeric(MoneyConfig.PRECISION, MoneyConfig.SCALE, asdecimal=True),
        nullable=False
    )
    currency = Column(String, index=True, nullable=False)
    order_id = Column(
        sqlalch_uuid(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True))
    external_id = Column(String, index=True, nullable=True, unique=True)
    is_accepted = Column(Boolean, index=True, nullable=False, default=False)
    is_refunded = Column(Boolean, index=True, nullable=False, default=False)
    accepted_at = Column(DateTime(timezone=True))
    refunded_at = Column(DateTime(timezone=True))
    order = relationship("SQLAlchOrderModel", back_populates="payments")


class SQLAlchOrderModel(SQLAlchBaseModel):
    __tablename__ = "orders"
    id = Column(sqlalch_uuid(as_uuid=True), primary_key=True, index=True)
    total_amount = Column(
        Numeric(MoneyConfig.PRECISION, MoneyConfig.SCALE, asdecimal=True),
        nullable=False
    )
    currency = Column(String, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True))
    paid_amount = Column(
        Numeric(MoneyConfig.PRECISION, MoneyConfig.SCALE, asdecimal=True),
        nullable=False
    )
    payments = relationship("SQLAlchPaymentModel", back_populates="order")
