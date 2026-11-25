"""로컬 DB 만들기 (KHS, PM 작업용). 저장소 맨 위에서: python scripts/init_db.py

서버(uvicorn)를 켤 때도 자동으로 만들어지므로 보통은 필요 없다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.core.storage.local_db import init_db  # noqa: E402

if __name__ == "__main__":
    init_db()
    print(f"로컬 DB를 만들었습니다: {get_settings().local_db_path}")
