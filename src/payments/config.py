import os
from pathlib import Path
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)
from pydantic import PostgresDsn
from enum import StrEnum
from functools import lru_cache



BASE_DIR = Path(__file__).resolve().parents[2]


class Mode(StrEnum):
    LOC = "loc"
    PROD = "prod"
    EXAMPLE = "example"


def get_env_file(mode: Mode) -> Path:
    match mode:
        case Mode.PROD:
            return BASE_DIR / ".env.prod"
        case Mode.EXAMPLE:
            return BASE_DIR / ".env.example"
        case _:
            return BASE_DIR / ".env.loc"


class Settings(BaseSettings):

    # bank_api
    bank_api_key: str
    bank_api_base_url: str

    # db
    postgres_host: str
    db_port: int
    postgres_user: str
    postgres_password: str
    postgres_db: str

    # app name
    app_name: str = "Payments & Orders"

    model_config = SettingsConfigDict(
        env_file = get_env_file(os.getenv("MODE", Mode.EXAMPLE)),
        env_file_encoding = "utf-8",
        extra = "ignore",
    )

    @property
    def db_url(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.db_port,
                path=self.postgres_db
            )
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
