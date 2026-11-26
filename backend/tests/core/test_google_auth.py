"""구글 OAuth 클라이언트 정보 읽기 (C-05). 가짜 값만 쓴다. 브라우저·구글 서버는 부르지 않는다."""

from pathlib import Path

import pytest

from app.core import gmail_client
from app.core.config import get_settings

FAKE_ID = "fake-client-id.apps.googleusercontent.com"
FAKE_SECRET = "fake-secret-not-real"


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_client_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", FAKE_ID)
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", FAKE_SECRET)
    cfg = gmail_client.client_config()
    assert cfg is not None
    assert cfg["installed"]["client_id"] == FAKE_ID
    assert cfg["installed"]["client_secret"] == FAKE_SECRET
    assert cfg["installed"]["token_uri"] == gmail_client.TOKEN_URI


@pytest.mark.parametrize("cid,secret", [("", ""), (FAKE_ID, ""), ("", FAKE_SECRET)])
def test_client_config_none_when_missing(
    monkeypatch: pytest.MonkeyPatch, cid: str, secret: str
) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", cid)
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", secret)
    assert gmail_client.client_config() is None


def test_login_without_any_client_says_why(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "")
    monkeypatch.setenv("GOOGLE_CREDENTIALS_FILE", str(tmp_path / "none.json"))
    with pytest.raises(gmail_client.GoogleAuthError) as e:
        gmail_client.login()
    assert "GOOGLE_CLIENT_ID" in str(e.value)
    assert FAKE_SECRET not in str(e.value)


class _FakeFlow:
    used: str = ""

    @classmethod
    def from_client_config(cls, config: dict, scopes: list[str]) -> "_FakeFlow":
        cls.used = "env"
        return cls()

    @classmethod
    def from_client_secrets_file(cls, path: str, scopes: list[str]) -> "_FakeFlow":
        cls.used = "file"
        return cls()

    def run_local_server(self, port: int) -> object:
        class _Creds:
            def to_json(self) -> str:
                return "{}"

        return _Creds()


@pytest.mark.parametrize("use_env,expected", [(True, "env"), (False, "file")])
def test_login_prefers_env_then_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, use_env: bool, expected: str
) -> None:
    import google_auth_oauthlib.flow as flow_mod

    cred_file = tmp_path / "credentials.json"
    cred_file.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", FAKE_ID if use_env else "")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", FAKE_SECRET if use_env else "")
    monkeypatch.setenv("GOOGLE_CREDENTIALS_FILE", str(cred_file))
    monkeypatch.setenv("GOOGLE_TOKEN_FILE", str(tmp_path / "token.json"))
    monkeypatch.setattr(flow_mod, "InstalledAppFlow", _FakeFlow)
    gmail_client.login()
    assert _FakeFlow.used == expected
    assert (tmp_path / "token.json").exists()
