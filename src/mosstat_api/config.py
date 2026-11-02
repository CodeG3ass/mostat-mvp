from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "Mosstat API"
    app_version: str = "0.1.0"
    debug: bool = False
    database_url: str = (
        "postgresql+psycopg://mosstat:mosstat@localhost:5432/mosstat"
    )
    raw_data_dir: Path = Path("data/raw")
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
