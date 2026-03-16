from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,JSON,
    BigInteger,
    ForeignKey,
    Enum as SQLEnum,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from typing import TypeVar
from datetime import datetime, UTC
from sqlalchemy import (
    Enum as SQLEnum,
    Numeric
)


Base = declarative_base()


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(SQLEnum, index=True, nullable=False)
    status = Column(SQLEnum, index=True, nullable=False)
    currency = Column(SQLEnum, index=True, nullable=False)
    amount = Column(Numeric(precision=18, scale=2), nullable=False)
    order = relationship("Order", back_populates="orders")


    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    email = Column(String(120), unique=True)
    tg_id = Column(Integer, unique=True)
    tg_first_name = Column(String(120))
    tg_last_name = Column(String(120))
    tg_photo_url = Column(String(120))
    tg_authdate = Column(Integer)
    tg_hash = Column(String(120))
    phone = Column(BigInteger )
    name = Column(String(120))
    surname = Column(String(120))

    # Relationship to auth sessions
    auth_sessions = relationship(
        "AuthSession", back_populates="user", cascade="all, delete-orphan"
    )

    api_credentials = relationship(
        "APICredentials", back_populates="user", cascade="all, delete-orphan" 
    )

    def __repr__(self) -> str:
        """String representation of User object."""
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
