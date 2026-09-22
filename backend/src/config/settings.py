from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Ecommerce API"
    debug: bool = False
    database_url: str = Field(default="", repr=False)
    stripe_secret_key: str = Field(default="", repr=False)
    stripe_webhook_secret: str = Field(default="", repr=False)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
