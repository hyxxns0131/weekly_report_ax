"""B1-05 식약처 제개정고시.

- mode="demo": samples/b1_input/demo/mfds_notice.json(저장해 둔 응답)을 읽는다.
- mode="auto": 실제 수집기 자리. 게시판 읽기 예정.
  채우기 전에 이용약관·robots.txt 확인, COLLECT_DELAY_SEC, 페이지 수 상한을 지킨다 (RULES.md 6장).
"""

from datetime import date
from typing import Any

from app.b1_select.collect.base import AUTO_NOT_READY, CollectResult, demo_path, load_demo

SOURCE_ID = "mfds_notice"


def collect(run_id: int, start: date, end: date, cfg: dict[str, Any]) -> CollectResult:
    if cfg.get("mode") == "demo":
        return load_demo(SOURCE_ID, demo_path(cfg), run_id, start, end)
    # TODO(auto): 실제 수집기를 여기에 둔다. 지금은 실패로 남겨 화면에 "수동 업로드"를 안내한다.
    return CollectResult(source=SOURCE_ID, status="failed", message=AUTO_NOT_READY)
