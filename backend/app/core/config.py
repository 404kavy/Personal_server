from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict #this is the new way to import SettingsConfigDict in pydantic v2 it function is to configure the settings model, including specifying the environment file and how to handle extra fields.
#for example, in this code snippet, the SettingsConfigDict is used to specify that the environment variables should be loaded from a .env file with UTF-8 encoding, and that any extra fields in the environment variables should be ignored. This allows for flexible configuration of the application settings while ensuring that only the relevant fields are used.


class Settings(BaseSettings):
    # Application
    app_name: str = "Personal Activity Server & Assistant"
    app_version: str = "0.1.0"
    debug: bool = False

    # API Prefix
    api_v1_prefix: str = "/api/v1"

    # Server Binding
    host: str = "127.0.0.1"
    port: int = 8000

    # Local AI Runtime (Ollama)
    ollama_base_url: str = "http://127.0.0.1:11434"
    default_model: str = "llama3.2:3b"

    # Database: Defaults to local SQLite for instant out-of-the-box operation;
    # Can be swapped to PostgreSQL in .env (e.g. postgresql://postgres:postgres@localhost:5432/personal_server)
    database_url: str = "sqlite:///./personal_server.db"

    # Security & Authentication
    secret_key: str = "dev-secret-token-change-in-env"
    access_token_expire_minutes: int = 30
    local_auth_token: str = "dev-secret-token-change-in-env"

    # CORS Configuration
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Environment configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Aliases for backwards compatibility
    @property
    def PROJECT_NAME(self) -> str:
        return self.app_name

    @property
    def VERSION(self) -> str:
        return self.app_version

    @property
    def API_V1_STR(self) -> str:
        return self.api_v1_prefix

    @property
    def HOST(self) -> str:
        return self.host

    @property
    def PORT(self) -> int:
        return self.port

    @property
    def OLLAMA_BASE_URL(self) -> str:
        return self.ollama_base_url

    @property
    def DEFAULT_MODEL(self) -> str:
        return self.default_model

    @property
    def DATABASE_URL(self) -> str:
        return self.database_url

    @property
    def LOCAL_AUTH_TOKEN(self) -> str:
        return self.local_auth_token

    @property
    def CORS_ORIGINS(self) -> List[str]:
        return self.cors_origins


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
