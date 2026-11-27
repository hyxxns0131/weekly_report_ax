"""구글 드라이브 읽기·보관 (C-04). 고객사 실제 목록은 드라이브에서만 읽는다.

- 읽기는 drive.readonly, 올리기(upload_file·ensure_folder, B2-08)는 drive.file 권한.
  인증은 core/gmail_client.py.
- 내려받은 파일은 `DATA_DIR/drive_cache/`에 (파일 ID, 수정 시각)으로 저장한다.
  드라이브에서 파일이 바뀌면 수정 시각이 달라져 새로 받고, 안 바뀌면 캐시를 쓴다.
"""

import io
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.core.config import get_settings
from app.core.gmail_client import DRIVE_FILE, DRIVE_READ, get_credentials

FOLDER = "application/vnd.google-apps.folder"
SHEET = "application/vnd.google-apps.spreadsheet"
DOC = "application/vnd.google-apps.document"
# 구글 문서 → 내보낼 형식
EXPORT = {SHEET: ("text/csv", ".csv"), DOC: ("text/plain", ".txt")}
FIELDS = "nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink)"
FILE_FIELDS = "id, name, mimeType, modifiedTime, webViewLink"


class DriveError(Exception):
    pass


class DriveFile(BaseModel):
    id: str
    name: str
    mime_type: str
    modified_time: str
    web_view_link: str | None = None
    path: str  # 폴더 기준 상대 경로 (하위 폴더/파일명)


def _service(write: bool = False) -> Any:
    from googleapiclient.discovery import build

    scopes = [DRIVE_READ, DRIVE_FILE] if write else [DRIVE_READ]
    return build("drive", "v3", credentials=get_credentials(scopes), cache_discovery=False)


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


UPLOAD_HINT = (
    "보관 폴더에 올릴 권한이 없을 수 있습니다. 폴더 ID·공유(편집 권한)를 확인하고, "
    "그래도 안 되면 drive.file 대신 drive 권한이 필요한지 PM에게 알려 주세요."
)


def _q(text: str) -> str:
    """드라이브 검색식 안 작은따옴표·역슬래시 처리."""
    return text.replace("\\", "\\\\").replace("'", "\\'")


def _find(svc: Any, parent_id: str, name: str, folder: bool) -> dict[str, Any] | None:
    kind = f"mimeType = '{FOLDER}'" if folder else f"mimeType != '{FOLDER}'"
    res = (
        svc.files()
        .list(
            q=f"'{parent_id}' in parents and name = '{_q(name)}' and {kind} and trashed = false",
            fields=FIELDS,
            pageSize=1,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )
    files: list[dict[str, Any]] = res.get("files", [])
    return files[0] if files else None


def ensure_folder(parent_id: str, name: str) -> str:
    """parent_id 아래 name 폴더 ID. 없으면 만든다 (예: 주차별 폴더 "2026년 11월 4주차")."""
    from googleapiclient.errors import HttpError

    if not parent_id:
        raise DriveError("보관 폴더 ID가 비어 있습니다. .env의 DRIVE_REPORTS_FOLDER_ID 확인")
    svc = _service(write=True)
    try:
        found = _find(svc, parent_id, name, folder=True)
        if found:
            return str(found["id"])
        made = (
            svc.files()
            .create(
                body={"name": name, "mimeType": FOLDER, "parents": [parent_id]},
                fields="id",
                supportsAllDrives=True,
            )
            .execute()
        )
    except HttpError as e:
        raise DriveError(
            f"드라이브 폴더 만들기 실패({e.status_code}): {name}. {UPLOAD_HINT}"
        ) from e
    return str(made["id"])


def upload_file(
    folder_id: str,
    name: str,
    content: bytes | str,
    mime_type: str = "text/plain",
    replace: bool = False,
) -> DriveFile:
    """folder_id 폴더에 파일을 올린다. str은 UTF-8로 올린다.

    replace=True면 같은 이름 파일(이 프로그램이 올린 것)을 새 내용으로 바꾸고, 없으면 새로 만든다.
    """
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseUpload

    if not folder_id:
        raise DriveError("보관 폴더 ID가 비어 있습니다. .env의 DRIVE_REPORTS_FOLDER_ID 확인")
    data = content.encode("utf-8") if isinstance(content, str) else content
    media = MediaIoBaseUpload(io.BytesIO(data), mimetype=mime_type, resumable=False)
    svc = _service(write=True)
    try:
        old = _find(svc, folder_id, name, folder=False) if replace else None
        if old:
            f = (
                svc.files()
                .update(
                    fileId=old["id"], media_body=media, fields=FILE_FIELDS, supportsAllDrives=True
                )
                .execute()
            )
        else:
            f = (
                svc.files()
                .create(
                    body={"name": name, "parents": [folder_id]},
                    media_body=media,
                    fields=FILE_FIELDS,
                    supportsAllDrives=True,
                )
                .execute()
            )
    except HttpError as e:
        raise DriveError(f"드라이브 올리기 실패({e.status_code}): {name}. {UPLOAD_HINT}") from e
    return DriveFile(
        id=f["id"],
        name=f["name"],
        mime_type=f["mimeType"],
        modified_time=f["modifiedTime"],
        web_view_link=f.get("webViewLink"),
        path=f["name"],
    )
