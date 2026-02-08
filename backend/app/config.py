from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///autonomy_health.db"
    DATA_DIR: str = "/Users/rahulmehta/Documents/Personal/potanu/2026/fhir-parser/backend/raw_data/sample-bulk-fhir-datasets-1000-patients"
    OPENAI_API_KEY: str = "test-open-ai-key"

    class Config:
        env_file = ".env"

settings = Settings()
