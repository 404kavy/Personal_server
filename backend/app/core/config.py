from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict #this is the new way to import SettingsConfigDict in pydantic v2 it function is to configure the settings model, including specifying the environment file and how to handle extra fields.
#for example, in this code snippet, the SettingsConfigDict is used to specify that the environment variables should be loaded from a .env file with UTF-8 encoding, and that any extra fields in the environment variables should be ignored. This allows for flexible configuration of the application settings while ensuring that only the relevant fields are used.
#function of base setting is 

class Settings(BaseSettings):
    PROJECT_NAME: str = "Personal Activity Server & Assistant"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Server Binding
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Local AI Runtime (Ollama)
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    DEFAULT_MODEL: str = "llama3.2:3b"

    # Database: Defaults to local SQLite for instant out-of-the-box operation;
    # Can be swapped to PostgreSQL in .env (e.g. postgresql://postgres:postgres@localhost:5432/personal_server)
    DATABASE_URL: str = "sqlite:///./personal_server.db"

    # Local Security & Pre-shared Token for collectors
    LOCAL_AUTH_TOKEN: str = "dev-secret-token-change-in-env"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
