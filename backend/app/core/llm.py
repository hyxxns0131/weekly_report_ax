"""LLM 호출 유일한 위치 (C-02). AGENTS.md 7장.

- 다른 파일은 AI 회사 API를 직접 부르지 않고 이 파일의 함수만 쓴다.
- 새 라이브러리 없이 httpx로 OpenAI·Anthropic REST API를 부른다.
- 키는 `.env`(OPENAI_API_KEY, ANTHROPIC_API_KEY)에서만 읽고, 화면·로그·응답에 내보내지 않는다.
- 화면에서 고른 회사·모델은 `LOCAL_DB_PATH`와 같은 폴더의 `ai_settings.json`에 저장한다
  (.gitignore의 data/ 안). 없으면 `.env`의 AI_PROVIDER·OPENAI_MODEL·CLAUDE_MODEL을 쓴다.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field

from app.core.config import REPO_ROOT, get_settings

log = logging.getLogger("llm")

Provider = Literal["openai", "claude"]
PROVIDERS: tuple[Provider, ...] = ("openai", "claude")
PROVIDER_LABEL: dict[str, str] = {"openai": "OpenAI (GPT)", "claude": "Anthropic (Claude)"}

MODELS_JSON = REPO_ROOT / "backend" / "config" / "ai_models.json"
OPENAI_BASE = "https://api.openai.com/v1"
ANTHROPIC_BASE = "https://api.anthropic.com/v1"
ANTHROPIC_VERSION = "2023-06-01"
TIMEOUT = httpx.Timeout(20.0, connect=10.0)


class AiError(Exception):
    """AI 호출 실패. 메시지는 화면에 그대로 보여도 되는 한국어 문장이다(키 값 없음)."""


class AiTest(BaseModel):
    ok: bool
    message: str
    provider: Provider
    model: str
    checked_at: str
    elapsed_ms: int = 0
    available_models: list[str] = Field(default_factory=list)


class AiStatus(BaseModel):
    enabled: bool  # LLM_ENABLED
    provider: Provider
    provider_label: str
    model: str
    key_set: bool  # 고른 회사의 키가 .env에 있는지 (값은 보내지 않는다)
    state: Literal["off", "no_key", "no_model", "ready", "ok", "error"]
    state_label: str
    models: list[str]  # 고를 수 있는 모델 (설정 파일 + 마지막 연결 검사에서 받은 목록)
    providers: list[Provider] = Field(default_factory=lambda: list(PROVIDERS))
    last_test: AiTest | None = None


# ---------------------------------------------------------------- 설정 저장


def _settings_file() -> Path:
    return get_settings().local_db_path.parent / "ai_settings.json"


def _load_saved() -> dict[str, Any]:
    f = _settings_file()
    if not f.exists():
        return {}
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(data: dict[str, Any]) -> None:
    f = _settings_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _config_models() -> dict[str, list[str]]:
    try:
        data = json.loads(MODELS_JSON.read_text(encoding="utf-8"))
        return {p: [str(m) for m in data.get(p, [])] for p in PROVIDERS}
    except (OSError, ValueError):
        return {p: [] for p in PROVIDERS}


def current() -> tuple[Provider, str]:
    """지금 쓸 회사와 모델. 화면에서 고른 값 > .env 값."""
    s = get_settings()
    saved = _load_saved()
    p = saved.get("provider") or s.ai_provider
    provider: Provider = p if p in PROVIDERS else "claude"
    models = saved.get("models", {}) if isinstance(saved.get("models"), dict) else {}
    env_model = s.openai_model if provider == "openai" else s.claude_model
    model = str(models.get(provider) or env_model or "")
    if not model:
        model = (_config_models().get(provider) or [""])[0]
    return provider, model


def _key(provider: Provider) -> str:
    s = get_settings()
    return s.openai_api_key if provider == "openai" else s.anthropic_api_key


def models_for(provider: Provider) -> list[str]:
    saved = _load_saved()
    fetched = saved.get("fetched_models", {}).get(provider, []) if saved else []
    out: list[str] = []
    for m in [*_config_models().get(provider, []), *fetched]:
        if m and m not in out:
            out.append(m)
    return out


def set_choice(provider: Provider, model: str) -> None:
    data = _load_saved()
    data["provider"] = provider
    data.setdefault("models", {})[provider] = model.strip()
    data.pop("last_test", None)  # 바꾸면 연결 검사를 다시 해야 한다
    _save(data)


def status() -> AiStatus:
    s = get_settings()
    provider, model = current()
    key_set = bool(_key(provider))
    saved = _load_saved()
    last: AiTest | None = None
    raw = saved.get("last_test")
    if isinstance(raw, dict):
        try:
            t = AiTest.model_validate(raw)
            if t.provider == provider and t.model == model:
                last = t
        except ValueError:
            last = None
    if not s.llm_enabled:
        state, label = "off", "꺼짐 (LLM_ENABLED=false) · 규칙만 사용"
    elif not key_set:
        key_name = "OPENAI_API_KEY" if provider == "openai" else "ANTHROPIC_API_KEY"
        state, label = "no_key", f"키 없음 · .env에 {key_name}를 넣어 주세요"
    elif not model:
        state, label = "no_model", "모델을 골라 주세요"
    elif last is None:
        state, label = "ready", "켜짐 · 연결 검사 전"
    elif last.ok:
        state, label = "ok", "연결됨"
    else:
        state, label = "error", "연결 실패"
    return AiStatus(
        enabled=s.llm_enabled,
        provider=provider,
        provider_label=PROVIDER_LABEL[provider],
        model=model,
        key_set=key_set,
        state=state,
        state_label=label,
        models=models_for(provider),
        last_test=last,
    )


# ---------------------------------------------------------------- 연결 검사


def _err_text(res: httpx.Response) -> str:
    if res.status_code == 401:
        return "키가 맞지 않습니다(401). .env의 키를 확인해 주세요."
    if res.status_code == 403:
        return "이 키로는 권한이 없습니다(403)."
    if res.status_code == 404:
        return "모델을 찾을 수 없습니다(404). 모델 이름을 확인해 주세요."
    if res.status_code == 429:
        return "사용량 한도나 결제 문제로 막혔습니다(429). 결제·한도를 확인해 주세요."
    try:
        body = res.json()
        msg = body.get("error", {}).get("message") if isinstance(body, dict) else None
    except ValueError:
        msg = None
    return f"오류 {res.status_code}" + (f": {str(msg)[:200]}" if msg else "")


def _list_models(provider: Provider, key: str) -> list[str]:
    if provider == "openai":
        res = httpx.get(
            f"{OPENAI_BASE}/models", headers={"Authorization": f"Bearer {key}"}, timeout=TIMEOUT
        )
        if res.status_code != 200:
            raise AiError(_err_text(res))
        ids = [m.get("id", "") for m in res.json().get("data", [])]
        # 글을 만드는 모델만 (음성·이미지·임베딩 제외)
        skip = ("embedding", "whisper", "tts", "dall-e", "audio", "realtime", "image", "moderation")
        ids = [i for i in ids if i.startswith(("gpt", "o")) and not any(k in i for k in skip)]
        return sorted(set(ids), reverse=True)
    res = httpx.get(
        f"{ANTHROPIC_BASE}/models",
        headers={"x-api-key": key, "anthropic-version": ANTHROPIC_VERSION},
        params={"limit": 100},
        timeout=TIMEOUT,
    )
    if res.status_code != 200:
        raise AiError(_err_text(res))
    return [m.get("id", "") for m in res.json().get("data", []) if m.get("id")]


def test_connection() -> AiTest:
    """키가 맞는지, 고른 모델을 이 키로 쓸 수 있는지 확인한다.

    모델 목록만 읽어서 비용(토큰)이 들지 않는다.
    """
    provider, model = current()
    key = _key(provider)
    now = datetime.now().isoformat(timespec="seconds")
    start = time.monotonic()
    fetched: list[str] = []
    if not get_settings().llm_enabled:
        ok, msg = False, "LLM_ENABLED=false라 AI를 쓰지 않습니다. .env에서 true로 바꿔 주세요."
    elif not key:
        name = "OPENAI_API_KEY" if provider == "openai" else "ANTHROPIC_API_KEY"
        ok, msg = False, f".env에 {name}가 없습니다."
    else:
        try:
            fetched = _list_models(provider, key)
            if not model:
                ok, msg = False, "키는 맞습니다. 모델을 골라 주세요."
            elif model in fetched:
                ok, msg = True, f"연결 성공 · {model} 사용 가능"
            else:
                ok, msg = False, f"키는 맞지만 이 키로 '{model}' 모델을 쓸 수 없습니다."
        except AiError as e:
            ok, msg = False, str(e)
        except httpx.HTTPError:
            ok, msg = False, "AI 서버에 접속하지 못했습니다. 인터넷·방화벽을 확인해 주세요."
    result = AiTest(
        ok=ok,
        message=msg,
        provider=provider,
        model=model,
        checked_at=now,
        elapsed_ms=int((time.monotonic() - start) * 1000),
        available_models=fetched,
    )
    data = _load_saved()
    data["last_test"] = result.model_dump(exclude={"available_models"})
    if fetched:
        data.setdefault("fetched_models", {})[provider] = fetched
    _save(data)
    log.info("AI 연결 검사 provider=%s model=%s ok=%s", provider, model, ok)
    return result


# ---------------------------------------------------------------- 호출


def call_json(
    system: str, user: str, prompt_version: str, max_tokens: int = 1500
) -> dict[str, Any]:
    """JSON 한 개를 돌려받는 호출. 고객사 정보가 들어가면 먼저 masking.mask()를 거친다(7장 4).

    LLM_ENABLED=false거나 키가 없으면 AiError. 부르는 쪽은 규칙 결과로 돌아간다.
    호출마다 모델·프롬프트 버전·토큰·소요 시간을 로그에 남긴다(7장 8).
    """
    if not get_settings().llm_enabled:
        raise AiError("AI가 꺼져 있습니다")
    provider, model = current()
    key = _key(provider)
    if not key or not model:
        raise AiError("AI 키나 모델이 설정되지 않았습니다")
    start = time.monotonic()
    try:
        if provider == "openai":
            res = httpx.post(
                f"{OPENAI_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "response_format": {"type": "json_object"},
                },
                timeout=httpx.Timeout(90.0, connect=10.0),
            )
            if res.status_code != 200:
                raise AiError(_err_text(res))
            body = res.json()
            text = body["choices"][0]["message"]["content"] or ""
            usage = body.get("usage", {})
            tokens = (usage.get("prompt_tokens"), usage.get("completion_tokens"))
        else:
            res = httpx.post(
                f"{ANTHROPIC_BASE}/messages",
                headers={"x-api-key": key, "anthropic-version": ANTHROPIC_VERSION},
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "system": system + "\n\nJSON 객체 하나만 출력한다.",
                    "messages": [{"role": "user", "content": user}],
                },
                timeout=httpx.Timeout(90.0, connect=10.0),
            )
            if res.status_code != 200:
                raise AiError(_err_text(res))
            body = res.json()
            text = "".join(b.get("text", "") for b in body.get("content", []))
            usage = body.get("usage", {})
            tokens = (usage.get("input_tokens"), usage.get("output_tokens"))
    except httpx.HTTPError as e:
        raise AiError("AI 서버에 접속하지 못했습니다") from e
    log.info(
        "AI 호출 provider=%s model=%s prompt=%s tokens=%s ms=%d",
        provider,
        model,
        prompt_version,
        tokens,
        int((time.monotonic() - start) * 1000),
    )
    s = text.strip()
    if s.startswith("```"):
        s = s.strip("`").removeprefix("json").strip()
    try:
        data = json.loads(s[s.find("{") : s.rfind("}") + 1])
    except ValueError as e:
        raise AiError("AI 결과 형식 오류") from e
    if not isinstance(data, dict):
        raise AiError("AI 결과 형식 오류")
    return data
