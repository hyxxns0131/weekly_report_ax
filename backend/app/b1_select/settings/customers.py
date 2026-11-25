"""B1-15 고객사 키워드 보기 (가명 ID). 원본은 구글 드라이브, 화면은 읽기 전용."""

from app.b1_select.match.customers import Customer, load_customers


def load() -> list[Customer]:
    return load_customers()
