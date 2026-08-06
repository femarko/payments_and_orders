from typing import TypeVar
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    sessionmaker,
    Session,
)



type SessionFactory = sessionmaker[Session]


def build_engine(db_url: str) -> Engine:
    return create_engine(db_url)


def session_factory(engine: Engine) -> SessionFactory:
    return sessionmaker[Session](
        autocommit=False,
        autoflush=False,
        bind=engine
    )
