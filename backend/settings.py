from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    QDRANT_DATABASE_URL: str
    QDRANT_API_KEY: str

    QDRANT_API_KEY: str
    QDRANT_DATABASE_URL: str

    @model_validator(mode="before")
    @classmethod
    def ensure_no_empty_vars(cls, values: dict):
        for field_name, field_value in values.items():
            if not field_value:
                raise ValueError(f".env var '{field_name}' cannot be empty.")
        return values


# Loaded only the first time the module is imported
load_dotenv()
settings = Settings()  # type: ignore
