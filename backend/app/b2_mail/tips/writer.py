"""B2-07 팁 문장 (LLM 연결 전에는 주제 + 근거 위치만 쓰고 담당자가 다듬는다)."""

from app.b2_mail.tips.topics import Topic


def draft(topic: Topic) -> str:
    return f"{topic.title}\n     근거: {topic.basis}"
