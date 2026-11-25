"""B2-06 항목 맞추기: 정답 key가 우리 항목의 제품명·제목에 들어 있으면 같은 항목으로 본다."""

from app.core.schema import SelectedItem


def text_of(i: SelectedItem) -> str:
    e = i.extracted
    return " ".join(
        x
        for x in [i.raw.title, e.product_name_ko if e else None, e.product_name_en if e else None]
        if x
    )


def align(keys: list[str], items: list[SelectedItem]) -> dict[str, SelectedItem | None]:
    return {k: next((i for i in items if k and k in text_of(i)), None) for k in keys}
