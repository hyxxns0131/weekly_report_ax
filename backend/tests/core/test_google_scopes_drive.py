"""구글 권한 범위·드라이브 올리기·설정 칸 (C-04·C-05, KHW B2-05·08 요청).

가짜 값만 쓴다. 구글 서버는 부르지 않는다.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from app.core import gmail_client
from app.core.config import get_settings
from app.core.storage import drive


@pytest.fixture(autouse=True)
def _clear_cache() -> Any:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_login_scopes_include_gmail_compose_and_drive_file() -> None:
    assert gmail_client.DRIVE_READ in gmail_client.SCOPES
    assert gmail_client.GMAIL_COMPOSE in gmail_client.SCOPES
    assert gmail_client.DRIVE_FILE in gmail_client.SCOPES


def _token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, scopes: list[str]) -> None:
    token = tmp_path / "token.json"
    token.write_text(
        json.dumps(
            {
                "token": "fake-access",
                "refresh_token": "fake-refresh",
                "client_id": "fake-id",
                "client_secret": "fake-secret",
                "token_uri": gmail_client.TOKEN_URI,
                "scopes": scopes,
                "expiry": "2999-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("GOOGLE_TOKEN_FILE", str(token))


def test_old_read_only_token_still_reads_drive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _token(tmp_path, monkeypatch, [gmail_client.DRIVE_READ])
    creds = gmail_client.get_credentials()
    assert creds.valid


def test_old_token_without_gmail_says_login_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _token(tmp_path, monkeypatch, [gmail_client.DRIVE_READ])
    with pytest.raises(gmail_client.GoogleAuthError) as e:
        gmail_client.get_credentials([gmail_client.GMAIL_COMPOSE])
    assert "gmail.compose" in str(e.value)
    assert "fake-secret" not in str(e.value)


def test_new_token_has_all(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _token(tmp_path, monkeypatch, gmail_client.SCOPES)
    assert gmail_client.get_credentials([gmail_client.GMAIL_COMPOSE]).valid
    assert gmail_client.get_credentials([gmail_client.DRIVE_READ, gmail_client.DRIVE_FILE]).valid


def test_config_reads_report_folder_sender_staff(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DRIVE_REPORTS_FOLDER_ID", "fake-folder  # 보관 폴더")
    monkeypatch.setenv("GMAIL_SENDER", " sender@example.com ")
    monkeypatch.setenv("GMAIL_STAFF_TO", "a@example.com,b@example.com")
    s = get_settings()
    assert s.drive_reports_folder_id == "fake-folder"
    assert s.gmail_sender == "sender@example.com"
    assert s.gmail_staff_to == "a@example.com,b@example.com"


class _Call:
    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result

    def execute(self) -> dict[str, Any]:
        return self.result


class _Files:
    """드라이브 files() 가짜. 만든 것·바꾼 것을 기록한다."""

    def __init__(self, existing: list[dict[str, Any]]) -> None:
        self.existing = existing
        self.created: list[dict[str, Any]] = []
        self.updated: list[str] = []

    def list(self, **kw: Any) -> _Call:
        q = kw["q"]
        hits = [f for f in self.existing if f"name = '{f['name']}'" in q]
        return _Call({"files": hits[:1]})

    def create(self, body: dict[str, Any], **kw: Any) -> _Call:
        self.created.append(body)
        return _Call(
            {
                "id": f"new{len(self.created)}",
                "name": body["name"],
                "mimeType": body.get("mimeType", "text/plain"),
                "modifiedTime": "2026-11-27T00:00:00Z",
            }
        )

    def update(self, fileId: str, **kw: Any) -> _Call:  # noqa: N803 (구글 API 인자 이름)
        self.updated.append(fileId)
        return _Call(
            {"id": fileId, "name": "보고서.md", "mimeType": "text/plain", "modifiedTime": "t"}
        )


class _Svc:
    def __init__(self, files: _Files) -> None:
        self._files = files

    def files(self) -> _Files:
        return self._files


def _fake(monkeypatch: pytest.MonkeyPatch, existing: list[dict[str, Any]]) -> _Files:
    files = _Files(existing)
    seen: list[bool] = []

    def fake_service(write: bool = False) -> _Svc:
        seen.append(write)
        assert write is True  # 올리기는 쓰기 권한으로
        return _Svc(files)

    monkeypatch.setattr(drive, "_service", fake_service)
    return files


def test_ensure_week_folder_creates_once(monkeypatch: pytest.MonkeyPatch) -> None:
    files = _fake(monkeypatch, [])
    fid = drive.ensure_folder("parent", "2026년 11월 4주차")
    assert fid == "new1"
    assert files.created[0]["mimeType"] == drive.FOLDER
    assert files.created[0]["parents"] == ["parent"]

    files2 = _fake(monkeypatch, [{"id": "old", "name": "2026년 11월 4주차"}])
    assert drive.ensure_folder("parent", "2026년 11월 4주차") == "old"
    assert files2.created == []


def test_upload_new_and_replace(monkeypatch: pytest.MonkeyPatch) -> None:
    files = _fake(monkeypatch, [])
    f = drive.upload_file("folder", "보고서.md", "A사 가상 본문", mime_type="text/markdown")
    assert f.id == "new1" and f.name == "보고서.md"
    assert files.created[0]["parents"] == ["folder"]

    files2 = _fake(monkeypatch, [{"id": "f9", "name": "보고서.md"}])
    f2 = drive.upload_file("folder", "보고서.md", b"bytes", replace=True)
    assert f2.id == "f9" and files2.updated == ["f9"] and files2.created == []


def test_upload_without_folder_says_why() -> None:
    with pytest.raises(drive.DriveError) as e:
        drive.upload_file("", "x.md", "본문")
    assert "DRIVE_REPORTS_FOLDER_ID" in str(e.value)
