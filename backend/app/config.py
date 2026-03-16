from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_api_key: str
    database_url: str = "sqlite:///./learning_platform.db"
    gemini_model: str = "gemini-3-flash-preview"
    firebase_credentials_path: str | None = None  # path to service account JSON

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
