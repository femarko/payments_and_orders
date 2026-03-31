from typing import TypeVar
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    sessionmaker,
    Session,
)

from payments.infrastructure.db.interfaces import DBSettingsProto



type SessionFactory = sessionmaker[Session]


def build_db_url(settings: DBSettingsProto) -> str:
    return (
        f"postgresql://{settings.POSTGRES_USER}:"
        f"{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:"
        f"{settings.DB_PORT}/{settings.POSTGRES_DB}"
    )


def build_engine(db_url: str) -> Engine:
    return create_engine(db_url)


def session_factory(engine: Engine) -> SessionFactory:
    return sessionmaker[Session](
        autocommit=False,
        autoflush=False,
        bind=engine
    )
