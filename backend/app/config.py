from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://zt_admin:zt_pass@localhost:5432/zt_dashboard"
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "zt-dashboard"
    KEYCLOAK_CLIENT_ID: str = "backend-api"
    SCORING_INTERVAL_SECONDS: int = 60
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
