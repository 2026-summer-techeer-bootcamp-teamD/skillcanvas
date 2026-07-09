from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수(.env)에서 설정을 읽어온다."""

    app_env: str = "local"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/skillcanvas"
    cors_origins: str = "http://localhost:5173"
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""

    # Claude(Anthropic) — 백엔드 AI 기능(assemble/recommend/map-node)용 개발자 공용키.
    # Max 구독과 별개(종량제). 팀장이 발급해 .env로 공유. 없으면 AI 호출 시 502.
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5"  # 기본=빠르고 쌈. assemble은 sonnet 권장

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
