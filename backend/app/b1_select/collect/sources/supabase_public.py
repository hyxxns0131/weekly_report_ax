"""Supabase 공개 정보 DB(weekly-report-ax)에서 보고 기간의 원문 가져오기.

PM(HS)이 Supabase에 적재한 공개 정보(부적합·검사지시·법령 개정·수집 원문)를 원문 항목으로 만든다.
DB가 비어 있으면 0건이다. 키가 없으면 실패로 남기고 다른 출처는 계속한다.
"""

from datetime import date

from app.b1_select.collect.base import CollectResult
from app.core.schema import RawItem, Source
from app.core.storage import public_db
from app.core.storage.local_db import now_kst

NAME = "supabase_public"


def _d(v: object) -> date | None:
    return date.fromisoformat(str(v)[:10]) if v else None


def collect(run_id: int, start: date, end: date) -> CollectResult:
    rng = {"and": f"(%s.gte.{start},%s.lte.{end})"}
    items: list[RawItem] = []
    try:
        for r in public_db.select(
            "pub_unfit", {"select": "*", "and": rng["and"] % ("unfit_date", "unfit_date")}
        ):
            body = "\n".join(
                f"{k}: {r[c]}"
                for k, c in [
                    ("제품명", "product_ko"),
                    ("제품명(영문)", "product_en"),
                    ("식품유형", "food_type"),
                    ("제조국", "country"),
                    ("제조업소", "maker"),
                    ("위반내역", "violation"),
                    ("처리기관", "office"),
                ]
                if r.get(c)
            )
            items.append(
                RawItem(
                    id=f"impfood_unfit:{r['id']}",
                    run_id=run_id,
                    source=Source.impfood_unfit,
                    title=f"부적합: {r.get('product_ko') or r.get('product_en') or r['id']}",
                    body=body,
                    posted_at=_d(r.get("unfit_date")),
                    url=r.get("url"),
                    collected_at=now_kst(),
                )
            )
        for r in public_db.select("pub_inspection_order", {"select": "*"}):
            ps, pe = _d(r.get("period_start")), _d(r.get("period_end"))
            if pe and pe < start or ps and ps > end:
                continue
            body = "\n".join(
                f"{k}: {r[c]}"
                for k, c in [
                    ("제조국", "country"),
                    ("식품유형", "food_type"),
                    ("검사항목", "items"),
                    ("기간", "period_start"),
                    ("사유", "reason"),
                ]
                if r.get(c)
            )
            items.append(
                RawItem(
                    id=f"impfood_inspection:{r['id']}",
                    run_id=run_id,
                    source=Source.impfood_inspection,
                    title=f"통관단계 검사지시: {r.get('country') or ''} {r.get('food_type') or ''}",
                    body=f"통관단계 검사지시\n{body}",
                    posted_at=ps,
                    url=r.get("url"),
                    collected_at=now_kst(),
                )
            )
        for r in public_db.select(
            "pub_source_item", {"select": "*", "and": rng["and"] % ("posted_at", "posted_at")}
        ):
            items.append(
                RawItem(
                    id=str(r["id"]),
                    run_id=run_id,
                    source=Source(r["source"])
                    if r["source"] in Source.__members__
                    else Source.manual,
                    title=r["title"],
                    body=r.get("body") or "",
                    posted_at=_d(r.get("posted_at")),
                    url=r.get("url"),
                    collected_at=now_kst(),
                )
            )
    except public_db.SupabaseNotConfiguredError as e:
        return CollectResult(source=NAME, status="failed", message=str(e))
    except Exception as e:  # noqa: BLE001 - 한 출처 실패가 전체를 멈추지 않게
        return CollectResult(source=NAME, status="failed", message=f"Supabase 읽기 실패: {e}")
    return CollectResult(source=NAME, status="ok", items=items, message=f"{len(items)}건")
