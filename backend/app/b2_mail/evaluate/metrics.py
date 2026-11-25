"""B2-06 재현율·정밀도·원인 태그."""

from app.b2_mail.evaluate.align import align, text_of
from app.b2_mail.evaluate.golden import Golden
from app.b2_mail.report.section1_unfit import label_of, matched_ids
from app.core.schema import EvalResult, Label, WeeklySelection


def _ratio(a: int, b: int) -> float | None:
    return round(a / b, 3) if b else None


def evaluate(run_id: int, golden: Golden, ws: WeeklySelection, elapsed: float) -> EvalResult:
    selected = [i for i in ws.items if label_of(i) == Label.relevant]
    pairs = align([g.key for g in golden.items], ws.items)
    hit = [k for k, i in pairs.items() if i is not None and label_of(i) == Label.relevant]
    missed = []
    for k, i in pairs.items():
        if i is None:
            missed.append(f"{k} [수집 안 됨]")
        elif label_of(i) != Label.relevant:
            missed.append(
                f"{k} [{'무관 오분류' if label_of(i) == Label.irrelevant else '검토 필요로 남음'}]"
            )
    golden_hits = {id(i) for i in pairs.values() if i is not None}
    extra = [f"{text_of(i)} [정답에 없음]" for i in selected if id(i) not in golden_hits]

    tp = fp = fn = 0
    wrong: list[str] = []
    for g in golden.items:
        item = pairs.get(g.key)
        ours = set(matched_ids(item)) if item else set()
        want = set(g.customers)
        tp += len(ours & want)
        fp += len(ours - want)
        fn += len(want - ours)
        if ours != want:
            tag = "[키워드 부족 또는 식품유형 표기 차이]"
            wrong.append(f"{g.key}: 정답 {sorted(want)} / 우리 {sorted(ours)} {tag}")
    return EvalResult(
        run_id=run_id,
        golden_week=golden.week,
        selection_recall=_ratio(len(hit), len(golden.items)),
        selection_precision=_ratio(len(hit), len(selected)),
        match_recall=_ratio(tp, tp + fn),
        match_precision=_ratio(tp, tp + fp),
        review_needed_ratio=_ratio(
            sum(1 for i in ws.items if label_of(i) == Label.review_needed), len(ws.items)
        ),
        missed_items=missed,
        extra_items=extra,
        wrong_matches=wrong,
        elapsed_sec=round(elapsed, 2),
    )
