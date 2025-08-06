from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "My RAG Bot"
    debug: bool = True
    secret_key: str
    access_token_expire_minutes: int = 30

    #ChrobaDB Settings
    chroma_persist_direcotry: str = "./data/chroma_db"

    #LLM and Embedding Model Settings
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_model_name: str = "microsoft/DialoGPT-medium"

    #AWS Settings
    aws_endpoint_url: str = "http://localhost:4566"
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"
    aws_region_name: str = "us-east-1"

    #Security Settings
    rate_limit_per_minute: int = 10
    max_document_size_mb: int = 25

    class Config:
        env_file = ".env"

settings = Settings()

