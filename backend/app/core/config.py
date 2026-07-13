from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수(.env)에서 설정을 읽어온다."""

    app_env: str = "local"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/skillcanvas"
    cors_origins: str = "http://localhost:5173"
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""

    # 콤마로 구분한 관리자 이메일. 이 이메일로 첫 로그인하면 is_admin=True 로 생성됨.
    admin_emails: str = ""
    # True면 JWT가 아닌 토큰(예: 테스트의 "alice")을 그대로 유저 식별자로 허용(개발 STUB).
    # 실제 Clerk JWT(점 2개)는 이 값과 무관하게 항상 서명 검증한다.
    auth_dev_mode: bool = True

    # Claude(Anthropic) — 백엔드 AI 기능(assemble/recommend/map-node)용 개발자 공용키.
    # Max 구독과 별개(종량제). 팀장이 발급해 .env로 공유. 없으면 AI 호출 시 502.
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5"  # 기본=빠르고 쌈. assemble은 sonnet 권장

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
