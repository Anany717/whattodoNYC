from __future__ import annotations

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="WhatToDo NYC API", alias="APP_NAME")
    env: str = Field(default="dev", alias="ENV")
    sqlalchemy_database_url: str = Field(
        default="sqlite:///./whattodo.db",
        alias="SQLALCHEMY_DATABASE_URL",
    )
    jwt_secret_key: str = Field(default="dev-secret-key", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=120, alias="JWT_EXPIRE_MINUTES")

    google_places_api_key: str | None = Field(default=None, alias="GOOGLE_PLACES_API_KEY")
    accuweather_api_key: str | None = Field(default=None, alias="ACCUWEATHER_API_KEY")
    accuweather_base_url: str = Field(
        default="https://dataservice.accuweather.com",
        alias="ACCUWEATHER_BASE_URL",
    )

    cors_origins_raw: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


settings = Settings()
