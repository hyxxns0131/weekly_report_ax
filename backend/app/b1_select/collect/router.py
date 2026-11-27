"""B1-01~07 수집 엔드포인트."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.b1_select.collect import service
from app.b1_select.collect.base import CollectResult
from app.b1_select.collect.sources import manual_upload, supabase_public
from app.core.schema import ExtractedInfo, RawItem, Selection, Source
from app.core.storage import local_db, repo

router = APIRouter()


class UploadRequest(BaseModel):
    source: Source = Source.manual
    kind: str = "text"  # csv | text | url
    content: str = ""
    url: str | None = None
    filename: str | None = None


class CollectRequest(BaseModel):
    sources: list[str] | None = None


class ItemRow(BaseModel):
    raw: RawItem
    selection: Selection | None
    extracted: ExtractedInfo | None


class SourceStatus(BaseModel):
    source: str
    name: str
    status: str
    count: int
    message: str
    at: str | None  # 마지막 수집 시각 (collect_log)
    latest_posted_at: str | None = None  # 이 실행에 들어온 그 출처 원문 중 가장 최근 게시일


def _run_or_404(run_id: int) -> None:
    if local_db.get_run(run_id) is None:
        raise HTTPException(status_code=404, detail="주간 실행을 찾을 수 없습니다.")


@router.post("/runs/{run_id}/upload", response_model=CollectResult)
def upload(run_id: int, body: UploadRequest) -> CollectResult:
    _run_or_404(run_id)
    if body.filename and body.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=415,
            detail="엑셀은 아직 읽을 수 없습니다. 엑셀에서 'CSV UTF-8'로 저장해 올려 주세요.",
        )
    if body.kind == "csv":
        result = manual_upload.from_csv(run_id, body.source, body.content)
    else:
        result = manual_upload.from_text(run_id, body.source, body.content, body.url)
    if not result.items:
        raise HTTPException(status_code=400, detail="올린 자료에서 항목을 찾지 못했습니다.")
    result.source = f"upload:{body.source.value}"
    return service.save(run_id, result)


@router.post("/runs/{run_id}/collect", response_model=list[CollectResult])
def collect(run_id: int, body: CollectRequest) -> list[CollectResult]:
    _run_or_404(run_id)
    return service.collect(run_id, body.sources)


@router.get("/runs/{run_id}/sources", response_model=list[SourceStatus])
def source_status(run_id: int) -> list[SourceStatus]:
    logs = {r["source"]: r for r in repo.list_collect_log(run_id)}
    names = {s["id"]: s["name"] for s in service.source_config()}
    names[supabase_public.NAME] = "Supabase 공개 정보 DB"
    latest: dict[str, str] = {}
    for raw in repo.list_raw(run_id):
        if raw.posted_at is None:
            continue
        sid, day = raw.source.value, raw.posted_at.isoformat()
        if day > latest.get(sid, ""):
            latest[sid] = day
    out = []
    for sid, name in names.items():
        if sid == "law_api":
            continue
        r = logs.get(sid)
        out.append(
            SourceStatus(
                source=sid,
                name=name,
                status=r["status"] if r else "waiting",
                count=r["count"] if r else 0,
                message=r["message"] if r else "",
                at=r["at"] if r else None,
                latest_posted_at=latest.get(sid),
            )
        )
    return out


@router.get("/runs/{run_id}/items", response_model=list[ItemRow])
def items(run_id: int, label: str | None = None) -> list[ItemRow]:
    _run_or_404(run_id)
    rows = []
    for raw in repo.list_raw(run_id):
        sel = repo.get_selection(raw.id)
        eff = (sel.final_label or sel.ai_label).value if sel else None
        if label and label != "all" and eff != label:
            continue
        rows.append(ItemRow(raw=raw, selection=sel, extracted=repo.get_extracted(raw.id)))
    return rows
