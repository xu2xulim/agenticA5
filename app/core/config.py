from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_VER_STR: str = "/v1"
    PROJECT_NAME: str = "FastAPI - Pydantic AI Agent"
    PROJECT_VERSION: str = "0.0.1"
    OPENAI_API_KEY: str
    # Instant
    INSTANT_APP_ID: str
    INSTANT_APP_SECRET: str
    # App
    HOSTNAME:str
    CUSTOM_INTEGRATION_KEY:str #GHL custom integration key
    LOCATION_ID:str #GHL location id
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
