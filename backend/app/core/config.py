"""환경 변수 읽기 (C-01). 환경 변수는 이 파일로만 읽는다(os.getenv 직접 호출 금지).

값은 저장소 맨 위 `.env`에 둔다. 이름과 설명은 `.env.example`이 기준이다.
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_CLAUDE_MODEL = "claude-sonnet-5-5"
DEFAULT_OPENAI_MODEL = ""


def _bool(value: str | None, default: bool) -> bool:
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(value: str | None, default: int) -> int:
    try:
        return int(value) if value else default
    except ValueError:
        return default


class Settings(BaseModel):
    app_env: str = "local"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]
    tz_name: str = "Asia/Seoul"
    data_dir: Path = REPO_ROOT / "data"
    local_db_path: Path = REPO_ROOT / "data" / "weekly.db"

    llm_enabled: bool = True
    ai_provider: str = "claude"
    claude_model: str = DEFAULT_CLAUDE_MODEL
    openai_model: str = DEFAULT_OPENAI_MODEL
    openai_api_key: str = ""  # 화면·로그·응답에 내보내지 않는다
    anthropic_api_key: str = ""

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    law_api_oc: str = ""
    collect_user_agent: str = "weekly_report-prototype"
    collect_delay_sec: float = 2.0
    mail_send_enabled: bool = False

    google_client_id: str = ""  # OAuth 데스크톱 앱 클라이언트 ID (.env만)
    google_client_secret: str = ""  # 화면·로그·응답에 내보내지 않는다
    google_credentials_file: Path = REPO_ROOT / "credentials.json"  # 예전 방식(위 2개가 비었을 때)
    google_token_file: Path = REPO_ROOT / "token.json"
    drive_law_folder_id: str = ""
    drive_reports_folder_id: str = ""  # 확정 보고서·보낸 메일 보관 폴더 (B2-08)
    gmail_sender: str = ""  # 발송 계정 (B2-05)
    gmail_staff_to: str = ""  # 담당자용 요약 메일 받는 사람 (쉼표로 여러 명)

    admin_username: str = ""
    admin_password: str = ""
    auth_secret_key: str = ""
    auth_session_hours: int = 12

    @property
    def login_configured(self) -> bool:
        return bool(self.admin_username and self.admin_password and self.auth_secret_key)


def _path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    p = Path(value)
    return p if p.is_absolute() else REPO_ROOT / p


@lru_cache
def get_settings() -> Settings:
    load_dotenv(REPO_ROOT / ".env", override=False)
    env = os.environ
    data_dir = _path(env.get("DATA_DIR"), REPO_ROOT / "data")
    return Settings(
        app_env=env.get("APP_ENV", "local"),
        api_host=env.get("API_HOST", "127.0.0.1"),
        api_port=_int(env.get("API_PORT"), 8000),
        cors_origins=[
            o.strip()
            for o in env.get("CORS_ORIGINS", "http://localhost:3000").split(",")
            if o.strip()
        ],
        tz_name=env.get("TZ_NAME", "Asia/Seoul"),
        data_dir=data_dir,
        local_db_path=_path(env.get("LOCAL_DB_PATH"), data_dir / "weekly.db"),
        llm_enabled=_bool(env.get("LLM_ENABLED"), True),
        ai_provider=env.get("AI_PROVIDER", "claude") or "claude",
        claude_model=env.get("CLAUDE_MODEL") or DEFAULT_CLAUDE_MODEL,
        openai_model=env.get("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL,
        openai_api_key=(env.get("OPENAI_API_KEY") or "").strip(),
        anthropic_api_key=(env.get("ANTHROPIC_API_KEY") or "").strip(),
        supabase_url=env.get("SUPABASE_URL", ""),
        supabase_anon_key=env.get("SUPABASE_ANON_KEY", ""),
        supabase_service_role_key=env.get("SUPABASE_SERVICE_ROLE_KEY", ""),
        law_api_oc=env.get("LAW_API_OC", ""),
        collect_user_agent=env.get("COLLECT_USER_AGENT", "weekly_report-prototype"),
        collect_delay_sec=float(env.get("COLLECT_DELAY_SEC") or 2),
        mail_send_enabled=_bool(env.get("MAIL_SEND_ENABLED"), False),
        google_client_id=(env.get("GOOGLE_CLIENT_ID") or "").strip(),
        google_client_secret=(env.get("GOOGLE_CLIENT_SECRET") or "").strip(),
        google_credentials_file=_path(
            env.get("GOOGLE_CREDENTIALS_FILE"), REPO_ROOT / "credentials.json"
        ),
        google_token_file=_path(env.get("GOOGLE_TOKEN_FILE"), REPO_ROOT / "token.json"),
        drive_law_folder_id=(env.get("DRIVE_LAW_FOLDER_ID") or "").split("#")[0].strip(),
        drive_reports_folder_id=(env.get("DRIVE_REPORTS_FOLDER_ID") or "").split("#")[0].strip(),
        gmail_sender=(env.get("GMAIL_SENDER") or "").strip(),
        gmail_staff_to=(env.get("GMAIL_STAFF_TO") or "").strip(),
        admin_username=env.get("ADMIN_USERNAME", ""),
        admin_password=env.get("ADMIN_PASSWORD", ""),
        auth_secret_key=env.get("AUTH_SECRET_KEY", ""),
        auth_session_hours=_int(env.get("AUTH_SESSION_HOURS"), 12),
    )
