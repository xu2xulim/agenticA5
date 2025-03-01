from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_VER_STR: str = "/v1"
    PROJECT_NAME: str = "AI Agent API with BrowserUse"
    PROJECT_VERSION: str = "0.0.1"
    OPENAI_API_KEY: str
    # Instant
    INSTANT_APP_ID: str
    INSTANT_APP_SECRET: str
    # App

    LOGFIRE_TOKEN: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
