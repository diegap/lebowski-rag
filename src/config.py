from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    OLLAMA_HOST: str = "http://localhost:11434"
    DB_PATH: str = "./db"
    MODEL: str = "llama3.2:3b"
    EMBED_MODEL: str = "nomic-embed-text"
    PDF: str = str(Path("data/thebiglebowski.pdf"))
    API_URL: str = "http://localhost:8000"
