"""Environment-based configuration (SAD §4 Authentication & Secrets)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    database_url: str = "postgresql+psycopg://peers:peers@localhost:5432/peers"
    session_secret: str = ""
    demo_access_code: str = ""
    allowed_origins: str = "http://localhost:3000"
    ai_spend_cap_usd: float = 20.0
    ai_model_suggest: str = "claude-sonnet-5-5"
    ai_model_assist: str = "claude-sonnet-5-5"
    ai_effort: str = "low"
    aamad_target_runtime: str = "crewai"
    # Set to false only for local http development; production cookies are always Secure.
    cookie_secure: bool = True
    trace_log_dir: str = "../project-context/2.build/logs"

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
