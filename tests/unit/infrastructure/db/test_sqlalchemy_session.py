from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from payments.infrastructure.db.sqlalchemy_session import (
    build_db_url,
    build_engine,
    session_factory,
)



def test_build_db_url(fake_settings):
    result = build_db_url(fake_settings)
    expected = "postgresql://postgres:postgres@localhost:5432/test_payments"
    assert result == expected


def test_build_engine():
    url = "postgresql://user:pass@localhost:5432/db"
    result = build_engine(url)

    assert isinstance(result, Engine)
    assert result.url.drivername == "postgresql"
    assert result.url.username == "user"
    assert result.url.password == "pass"
    assert result.url.host == "localhost"
    assert result.url.port == 5432
    assert result.url.database == "db"


def test_session_factory(fake_settings):
    engine = build_engine(build_db_url(fake_settings))
    sess_factory = session_factory(engine)
    session = sess_factory()
    assert isinstance(sess_factory, sessionmaker)
    assert sess_factory.kw["autocommit"] is False
    assert sess_factory.kw["autoflush"] is False
    assert sess_factory.kw["bind"] is engine
    assert isinstance(session, Session)
    assert session.bind is engine


def test_full_wiring(fake_settings):
    engine = build_engine(build_db_url(fake_settings))
    session = session_factory(engine)
    assert session.kw["bind"] is engine
