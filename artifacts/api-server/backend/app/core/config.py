import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    ELASTICSEARCH_URL: str = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")

    AZURE_OPENAI_ENDPOINT: str = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str = os.environ.get("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_DEPLOYMENT: str = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
    AZURE_OPENAI_API_VERSION: str = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01")

    FRESHSERVICE_BASE_URL: str = os.environ.get("FRESHSERVICE_BASE_URL", "")
    FRESHSERVICE_API_KEY: str = os.environ.get("FRESHSERVICE_API_KEY", "")

    GRAPH_API_TENANT_ID: str = os.environ.get("GRAPH_API_TENANT_ID", "")
    GRAPH_API_CLIENT_ID: str = os.environ.get("GRAPH_API_CLIENT_ID", "")
    GRAPH_API_CLIENT_SECRET: str = os.environ.get("GRAPH_API_CLIENT_SECRET", "")

    GOOGLE_CLIENT_ID: str = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.environ.get("GOOGLE_CLIENT_SECRET", "")

    TEAMS_APP_ID: str = os.environ.get("TEAMS_APP_ID", "")
    TEAMS_APP_PASSWORD: str = os.environ.get("TEAMS_APP_PASSWORD", "")
    TEAMS_TENANT_ID: str = os.environ.get("TEAMS_TENANT_ID", "")

    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "stack-default-secret-key-change-in-production-32chars")
    JWT_ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.environ.get("JWT_EXPIRE_MINUTES", "480"))

    ALLOWED_EMAIL_DOMAIN: str = os.environ.get("ALLOWED_EMAIL_DOMAIN", "jadeglobal.com")
    FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://localhost:3000")
    CHATBOT_WEBHOOK_SECRET: str = os.environ.get("CHATBOT_WEBHOOK_SECRET", "")

    WINRM_USERNAME: str = os.environ.get("WINRM_USERNAME", "")
    WINRM_PASSWORD: str = os.environ.get("WINRM_PASSWORD", "")

    AGENT_HOURLY_COST: float = float(os.environ.get("AGENT_HOURLY_COST", "500.0"))
    AVG_MANUAL_RESOLUTION_MINS: float = float(os.environ.get("AVG_MANUAL_RESOLUTION_MINS", "45.0"))

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
