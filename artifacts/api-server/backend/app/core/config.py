import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    ELASTICSEARCH_URL: str = "http://localhost:9200"

    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "text-embedding-3-large"
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"

    FRESHSERVICE_BASE_URL: str = ""
    FRESHSERVICE_API_KEY: str = ""

    GRAPH_API_TENANT_ID: str = ""
    GRAPH_API_CLIENT_ID: str = ""
    GRAPH_API_CLIENT_SECRET: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    TEAMS_APP_ID: str = ""
    TEAMS_APP_PASSWORD: str = ""
    TEAMS_TENANT_ID: str = ""

    JWT_SECRET_KEY: str = "stack-default-secret-key-change-in-production-32chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    ALLOWED_EMAIL_DOMAIN: str = "jadeglobal.com"
    FRONTEND_URL: str = "http://localhost:3000"
    CHATBOT_WEBHOOK_SECRET: str = ""

    WINRM_USERNAME: str = ""
    WINRM_PASSWORD: str = ""

    AGENT_HOURLY_COST: float = 500.0
    AVG_MANUAL_RESOLUTION_MINS: float = 45.0

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
