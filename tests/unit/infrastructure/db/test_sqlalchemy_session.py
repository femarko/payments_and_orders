from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from payments.infrastructure.db.sqlalchemy_session import (
    build_engine,
    session_factory,
)



def test_build_engine(fake_db_url):
    result = build_engine(fake_db_url)

    assert isinstance(result, Engine)
    assert result.url.drivername == "postgresql+psycopg"
    assert result.url.username == "user"
    assert result.url.password == "pass"
    assert result.url.host == "localhost"
    assert result.url.port == 5432
    assert result.url.database == "db"


def test_session_factory(fake_db_url):
    engine = build_engine(fake_db_url)
    sess_factory = session_factory(engine)
    session = sess_factory()
    assert isinstance(sess_factory, sessionmaker)
    assert sess_factory.kw["autocommit"] is False
    assert sess_factory.kw["autoflush"] is False
    assert sess_factory.kw["bind"] is engine
    assert isinstance(session, Session)
    assert session.bind is engine


def test_full_wiring(fake_db_url):
    engine = build_engine(fake_db_url)
    session = session_factory(engine)
    assert session.kw["bind"] is engine
