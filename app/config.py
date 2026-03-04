from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Critical Workflow Watchdog"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/watchdog"
    redis_url: str = "redis://localhost:6379/0"
    api_timeout_seconds: int = 5
    latency_threshold_seconds: int = 3
    smtp_host: str = "localhost"
    smtp_port: int = 25
    alert_from_email: str = "watchdog@localhost"
    alert_to_email: str = "oncall@localhost"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
