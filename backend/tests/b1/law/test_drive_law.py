"""B1-12 구글 드라이브 법령 폴더 → LawChange. 드라이브는 가짜로 바꾼다(실제 호출 없음)."""

from datetime import date

import pytest

from app.b1_select.law import drive_law
from app.core.storage import drive


def _file(name: str, mime: str, fid: str = "f1") -> drive.DriveFile:
    return drive.DriveFile(
        id=fid,
        name=name,
        mime_type=mime,
        modified_time="2026-11-20T00:00:00.000Z",
        web_view_link=f"https://drive.example/{fid}",
        path=name,
    )


SHEET_CSV = (
    "행정규칙일련번호,고시명,제개정 구분,고시번호,고시일,시행일,개정 이유,출처\n"
    "2100000001,가상 식품 기준 고시,일부개정,제2026-1호,2026.11.10,2026-11-17,"
    "가상 개정 이유입니다,https://law.example/1\n"
    ",가상 표시 기준 고시,,,,20261118,,\n"
    ",,,,,,,\n"
)


def test_parse_date_variants() -> None:
    assert drive_law.parse_date("2026.11.17") == date(2026, 11, 17)
    assert drive_law.parse_date("2026-1-7") == date(2026, 1, 7)
    assert drive_law.parse_date("20261117") == date(2026, 11, 17)
    assert drive_law.parse_date("2026년 11월 17일") == date(2026, 11, 17)
    assert drive_law.parse_date("확인 필요") is None
    assert drive_law.parse_date("2026.13.40") is None


def test_from_table_maps_columns() -> None:
    f = _file("법령 목록", drive.SHEET)
    rows = drive_law.from_table(SHEET_CSV, f)
    assert len(rows) == 2  # 빈 행은 건너뛴다
    a, b = rows
    assert a.id == "law:2100000001"  # 법제처 API와 같은 ID
    assert a.law_name == "가상 식품 기준 고시"
    assert a.change_type == "일부개정"
    assert a.number == "제2026-1호"
    assert a.promulgated_at == date(2026, 11, 10)
    assert a.effective_at == date(2026, 11, 17)
    assert a.ai_summary == "가상 개정 이유입니다"
    assert a.source_url == "https://law.example/1"
    # 없는 값은 None("확인 필요"), 출처 칸이 비면 드라이브 링크
    assert b.id.startswith("drive:")
    assert b.number is None and b.ai_summary is None
    assert b.effective_at == date(2026, 11, 18)
    assert b.source_url == "https://drive.example/f1"


def test_from_table_without_name_column() -> None:
    assert drive_law.from_table("a,b\n1,2\n", _file("x.csv", "text/csv")) == []


def test_from_text_reads_effective_date() -> None:
    f = _file("가상 고시 개정 안내", drive.DOC)
    c = drive_law.from_text("가상 고시를 개정합니다.\n시행일: 2026. 11. 19.\n", f)
    assert c.law_name == "가상 고시 개정 안내"
    assert c.effective_at == date(2026, 11, 19)
    assert c.source_url == "https://drive.example/f1"


def test_fetch_reads_supported_and_skips_others(monkeypatch: pytest.MonkeyPatch) -> None:
    files = [
        _file("목록", drive.SHEET, "s1"),
        _file("목록2.csv", "text/csv", "c1"),
        _file("원문.pdf", "application/pdf", "p1"),
    ]
    monkeypatch.setattr(drive, "list_folder", lambda folder_id: files)
    data = {"s1": SHEET_CSV.encode("utf-8"), "c1": SHEET_CSV.encode("cp949")}
    monkeypatch.setattr(drive, "fetch_bytes", lambda f: data[f.id])

    res = drive_law.fetch("folder")
    assert res.files == 2
    assert res.skipped == ["원문.pdf"]
    assert len(res.changes) == 4
    assert res.changes[2].law_name == "가상 식품 기준 고시"  # cp949 CSV도 읽는다
