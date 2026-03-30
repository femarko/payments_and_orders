import os


def require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is required")
    return value


class Settings:
    # auth / tokens
    BANK_API_KEY = require("BANK_API_KEY")

    # db
    POSTGRES_HOST = require("POSTGRES_HOST")
    DB_PORT = int(require("DB_PORT"))
    POSTGRES_USER = require("POSTGRES_USER")
    POSTGRES_PASSWORD = require("POSTGRES_PASSWORD")
    POSTGRES_DB = require("POSTGRES_DB")

    # app name
    APP_NAME = "Payments & Orders"
