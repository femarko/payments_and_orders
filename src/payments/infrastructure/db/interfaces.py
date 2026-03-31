from typing import Protocol



class DBSettingsProto(Protocol):
    POSTGRES_HOST: str
    DB_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
