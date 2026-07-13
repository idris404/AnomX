"""Application settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven configuration for the API service."""

    model_config = SettingsConfigDict(env_prefix="ANOMX_", env_file=".env", extra="ignore")

    app_name: str = "AnomX API"
    app_version: str = "0.1.0"
    debug: bool = False

    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_user: str = "anomx"
    postgres_password: str = "anomx"
    postgres_db: str = "anomx"

    redis_host: str = "localhost"
    redis_port: int = 6379

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"
