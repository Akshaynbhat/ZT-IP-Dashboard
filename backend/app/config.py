from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://zt_admin:zt_pass@localhost:5432/zt_dashboard"
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "zt-dashboard"
    KEYCLOAK_CLIENT_ID: str = "backend-api"
    SCORING_INTERVAL_SECONDS: int = 60
    LOG_LEVEL: str = "INFO"
    REDIS_URL: str = "redis://localhost:6379/0"
    GITHUB_WEBHOOK_SECRET: str = "github_secret_123"
    GITLAB_WEBHOOK_SECRET: str = "gitlab_secret_123"



    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
