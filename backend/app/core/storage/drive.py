"""구글 드라이브 읽기·보관 (C-04). 고객사 실제 목록은 드라이브에서만 읽는다.

- 읽기 전용(drive.readonly). 인증은 core/gmail_client.py.
- 내려받은 파일은 `DATA_DIR/drive_cache/`에 (파일 ID, 수정 시각)으로 저장한다.
  드라이브에서 파일이 바뀌면 수정 시각이 달라져 새로 받고, 안 바뀌면 캐시를 쓴다.
"""

import io
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.core.config import get_settings
from app.core.gmail_client import get_credentials

FOLDER = "application/vnd.google-apps.folder"
SHEET = "application/vnd.google-apps.spreadsheet"
DOC = "application/vnd.google-apps.document"
# 구글 문서 → 내보낼 형식
EXPORT = {SHEET: ("text/csv", ".csv"), DOC: ("text/plain", ".txt")}
FIELDS = "nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink)"


class DriveError(Exception):
    pass


class DriveFile(BaseModel):
    id: str
    name: str
    mime_type: str
    modified_time: str
    web_view_link: str | None = None
    path: str  # 폴더 기준 상대 경로 (하위 폴더/파일명)


def _service() -> Any:
    from googleapiclient.discovery import build

    return build("drive", "v3", credentials=get_credentials(), cache_discovery=False)


def list_folder(folder_id: str, recursive: bool = True) -> list[DriveFile]:
    """폴더 안 파일 목록(휴지통 제외). 하위 폴더까지 읽는다."""
    from googleapiclient.errors import HttpError

    svc = _service()
    out: list[DriveFile] = []
    stack: list[tuple[str, str]] = [(folder_id, "")]
    try:
        while stack:
            fid, prefix = stack.pop()
            token: str | None = None
            while True:
                res = (
                    svc.files()
                    .list(
                        q=f"'{fid}' in parents and trashed = false",
                        fields=FIELDS,
                        pageSize=200,
                        pageToken=token,
                        supportsAllDrives=True,
                        includeItemsFromAllDrives=True,
                    )
                    .execute()
                )
                for f in res.get("files", []):
                    path = f"{prefix}{f['name']}"
                    if f["mimeType"] == FOLDER:
                        if recursive:
                            stack.append((f["id"], f"{path}/"))
                        continue
                    out.append(
                        DriveFile(
                            id=f["id"],
                            name=f["name"],
                            mime_type=f["mimeType"],
                            modified_time=f["modifiedTime"],
                            web_view_link=f.get("webViewLink"),
                            path=path,
                        )
                    )
                token = res.get("nextPageToken")
                if not token:
                    break
    except HttpError as e:
        msg = f"드라이브 폴더 읽기 실패({e.status_code}): 폴더 ID·공유 권한 확인 필요"
        raise DriveError(msg) from e
    return out


def _cache_dir() -> Path:
    d = get_settings().data_dir / "drive_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def fetch_bytes(f: DriveFile) -> bytes:
    """파일 내용. 구글 시트는 CSV(첫 시트), 구글 문서는 텍스트로 받는다. 수정 시각 기준 캐시."""
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseDownload

    stamp = re.sub(r"[^0-9A-Za-z]", "", f.modified_time)
    ext = EXPORT[f.mime_type][1] if f.mime_type in EXPORT else Path(f.name).suffix
    cached = _cache_dir() / f"{f.id}_{stamp}{ext}"
    if cached.exists():
        return cached.read_bytes()
    svc = _service()
    try:
        if f.mime_type in EXPORT:
            req = svc.files().export_media(fileId=f.id, mimeType=EXPORT[f.mime_type][0])
        else:
            req = svc.files().get_media(fileId=f.id, supportsAllDrives=True)
        buf = io.BytesIO()
        dl = MediaIoBaseDownload(buf, req)
        done = False
        while not done:
            _, done = dl.next_chunk()
    except HttpError as e:
        raise DriveError(f"드라이브 파일 받기 실패({e.status_code}): {f.path}") from e
    for old in _cache_dir().glob(f"{f.id}_*"):
        old.unlink(missing_ok=True)
    cached.write_bytes(buf.getvalue())
    return buf.getvalue()
