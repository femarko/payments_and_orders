from sqlalchemy.orm import (
    DeclarativeBase,
    relationship,
    Mapped,
    mapped_column,
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
from typing import (
    TypeVar,
    Optional
)
from decimal import Decimal
from uuid import UUID
from datetime import datetime

from payments.domain.value_objects import MoneyConfig
from payments.domain.enums import (
    PaymentStatus,
    PaymentType,
    Currency,
)


class SQLAlchBaseModel(DeclarativeBase): ...


T_SQLAlchBaseModel = TypeVar("T_SQLAlchBaseModel", bound=type[SQLAlchBaseModel])


class SQLAlchPaymentModel(SQLAlchBaseModel):
    __tablename__ = "payments"
    id: Mapped[UUID] = mapped_column(sqlalch_uuid(as_uuid=True), primary_key=True, index=True)
    type: Mapped[PaymentType] = mapped_column(String, index=True, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(String, index=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(MoneyConfig.PRECISION, MoneyConfig.SCALE, asdecimal=True),
        nullable=False
    )
    currency: Mapped[Currency] = mapped_column(String, index=True, nullable=False)
    order_id: Mapped[UUID] = mapped_column(
        sqlalch_uuid(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    external_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True, unique=True)
    is_accepted: Mapped[bool] = mapped_column(Boolean, index=True, nullable=False, default=False)
    is_refunded: Mapped[bool] = mapped_column(Boolean, index=True, nullable=False, default=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    order = relationship("SQLAlchOrderModel", back_populates="payments")


class SQLAlchOrderModel(SQLAlchBaseModel):
    __tablename__ = "orders"
    id: Mapped[UUID] = mapped_column(sqlalch_uuid(as_uuid=True), primary_key=True, index=True)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(MoneyConfig.PRECISION, MoneyConfig.SCALE, asdecimal=True),
        nullable=False
    )
    currency: Mapped[Currency] = mapped_column(String, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(MoneyConfig.PRECISION, MoneyConfig.SCALE, asdecimal=True),
        nullable=False
    )
    payments = relationship("SQLAlchPaymentModel", back_populates="order")
