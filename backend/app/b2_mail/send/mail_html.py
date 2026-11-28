"""B2-05 메일 본문 글 → HTML. 실제 메일(11월 4주차)처럼 부적합 표를 칸 있는 표로 보이게 한다.

초안 본문은 일반 글이고 표는 `| 칸 | 칸 |` 줄로 되어 있다(report/section1_unfit.py).
- `|`로 시작하는 줄이 이어지면 표 하나로 묶는다. 첫 줄은 머리줄, `|---|` 줄은 건너뛴다.
- 나머지 줄은 글 그대로 두고 줄바꿈·앞 칸 띄우기만 살린다.
- 모든 글은 HTML 이스케이프한 뒤 넣는다. 주소(http…)만 링크로 바꾼다.
새 라이브러리 없이 표준 라이브러리만 쓴다.
"""

import html
import re

_URL = re.compile(r"https?://[^\s<>\"']+")
_SEP = re.compile(r"^\|(\s*:?-+:?\s*\|)+$")

TABLE_STYLE = "border-collapse:collapse;margin:4px 0 8px 0;font-size:13px"
CELL_STYLE = "border:1px solid #999;padding:4px 6px;vertical-align:top"
HEAD_STYLE = CELL_STYLE + ";background:#f2f2f2;font-weight:bold"
BODY_STYLE = "font-family:'Malgun Gothic',sans-serif;font-size:14px;line-height:1.6"


def _inline(text: str) -> str:
    """이스케이프 + 주소만 링크."""
    out: list[str] = []
    pos = 0
    for m in _URL.finditer(text):
        out.append(html.escape(text[pos : m.start()]))
        url = html.escape(m.group(0))
        out.append(f'<a href="{url}">{url}</a>')
        pos = m.end()
    out.append(html.escape(text[pos:]))
    return "".join(out)


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _table(rows: list[str]) -> str:
    body = [r for r in rows if not _SEP.match(r.strip().replace(" ", ""))]
    if not body:
        return ""
    parts = [f'<table style="{TABLE_STYLE}">']
    for i, row in enumerate(body):
        style, tag = (HEAD_STYLE, "th") if i == 0 else (CELL_STYLE, "td")
        cells = "".join(f'<{tag} style="{style}">{_inline(c)}</{tag}>' for c in _cells(row))
        parts.append(f"<tr>{cells}</tr>")
    parts.append("</table>")
    return "".join(parts)


def _text_line(line: str) -> str:
    stripped = line.lstrip(" ")
    indent = "&nbsp;" * (len(line) - len(stripped))
    return indent + _inline(stripped)


def to_html(body: str) -> str:
    """일반 글 본문 → HTML 문서 한 개."""
    lines = body.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    table: list[str] = []
    for line in lines:
        if line.strip().startswith("|"):
            table.append(line)
            continue
        if table:
            out.append(_table(table))
            table = []
        out.append(_text_line(line) + "<br>")
    if table:
        out.append(_table(table))
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
        f'<body><div style="{BODY_STYLE}">{"".join(out)}</div></body></html>'
    )
