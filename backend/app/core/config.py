from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Pramana"
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://pramana:pramana@localhost:5432/pramana"
    redis_url: str = "redis://localhost:6379/0"

    groq_api_key: str = ""
    gemini_api_key: str = ""

    groq_model: str = "llama-3.3-70b-versatile"
    gemini_model: str = "gemini-2.0-flash"

    # Verification thresholds — tune these once the eval harness produces real numbers.
    grounding_similarity_threshold: float = 0.82


settings = Settings()
