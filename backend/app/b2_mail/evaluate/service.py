"""B2-06 과거 보고서 대비 검증."""

import time

from app.b2_mail.evaluate import golden, metrics
from app.b2_mail.input import load_selection
from app.core.schema import EvalResult
from app.core.storage import repo


class NoGolden(Exception):
    pass


def run_eval(run_id: int, week: str, token: str | None, source: str = "api") -> EvalResult:
    g = golden.find(week)
    if g is None:
        raise NoGolden("과거 보고서 정답 자료가 없습니다(SAMC 전달 대기).")
    t0 = time.perf_counter()
    ws = load_selection(run_id, token, source)
    result = metrics.evaluate(run_id, g, ws, time.perf_counter() - t0)
    repo.save_eval(result)
    return result
