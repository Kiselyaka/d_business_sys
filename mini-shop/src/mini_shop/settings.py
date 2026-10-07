from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+pysqlite:///:memory:"
    integration_platform_url: str = "http://localhost:8000"
    integration_publish_timeout_seconds: float = 5.0
    log_level: str = "INFO"
