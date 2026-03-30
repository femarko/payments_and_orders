from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from payments.infrastructure.db.orm_models import SQLAlchBaseModel
from payments.config import Settings



SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{Settings.POSTGRES_USER}:"
    f"{Settings.POSTGRES_PASSWORD}@{Settings.POSTGRES_HOST}:"
    f"{Settings.DB_PORT}/{Settings.POSTGRES_DB}"
)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
start_session = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
