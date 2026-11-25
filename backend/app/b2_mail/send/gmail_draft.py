"""B2-05 Gmail 초안함 저장. core/gmail_client.py(C-05, 구글 인증) 준비 후 연결한다."""


class GmailNotReady(Exception):
    pass


def save_to_gmail(subject: str, body: str) -> str:
    raise GmailNotReady("구글 연결(C-05) 전입니다. 지금은 [복사]로 Gmail에 붙여 넣어 주세요.")
