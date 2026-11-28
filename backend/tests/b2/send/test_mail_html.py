"""B2-05 본문 글 → HTML 변환 (표·이스케이프·링크)."""

from app.b2_mail.send.mail_html import to_html

BODY = """수신자 제위

  ■ 부적합 (1건)
   | 제조국가 | 제조/수출회사 | 위반 내역 | 출처 |
   |---|---|---|---|
   | 중국 | <ABC> & Co. | 이산화황 초과 | https://example.com/a?b=1 |
감사합니다."""


def test_table_lines_become_html_table() -> None:
    out = to_html(BODY)
    assert out.count("<table") == 1
    assert out.count("<tr>") == 2  # 머리줄 + 1건, |---| 줄은 빠짐
    assert '<th style="' in out and "제조국가</th>" in out
    assert "---" not in out


def test_text_is_escaped_and_urls_linked() -> None:
    out = to_html(BODY)
    assert "&lt;ABC&gt; &amp; Co." in out
    assert "<ABC>" not in out
    assert '<a href="https://example.com/a?b=1">' in out


def test_plain_lines_keep_breaks_and_indent() -> None:
    out = to_html(BODY)
    assert "수신자 제위<br>" in out
    assert "&nbsp;&nbsp;■ 부적합 (1건)<br>" in out
    assert out.rstrip().endswith("</html>")
