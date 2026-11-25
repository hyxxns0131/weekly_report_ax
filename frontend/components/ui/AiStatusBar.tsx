"use client";
// AI 연결 상태 줄 (KHS, C-02). AI를 쓰는 탭 위에 둔다.
// 상태 표시 · AI 회사·모델 선택 · 연결 검사 버튼. 키 값은 화면에 오지 않는다(.env에만 있음).

import { useCallback, useEffect, useState } from "react";
import { getAiStatus, setAiChoice, testAi } from "../../lib/api/core";
import type { AiProvider, AiState, AiStatus, AiTest } from "../../lib/types/core";
import { Badge } from "./Badge";
import { color, type Tone } from "./tokens";

const TEXT = {
  ai: "AI",
  test: "연결 검사",
  testing: "검사 중…",
  model: "모델",
  provider: "AI 회사",
  custom: "직접 입력…",
  customPrompt: "모델 이름을 입력하세요 (예: gpt-4.1-mini)",
  loadFail: "AI 상태를 불러오지 못했습니다",
  providerLabel: { openai: "OpenAI (GPT)", claude: "Anthropic (Claude)" } as Record<AiProvider, string>,
};

const TONE: Record<AiState, Tone> = {
  off: "muted",
  no_key: "warning",
  no_model: "warning",
  ready: "info",
  ok: "success",
  error: "danger",
};

const DOT: Record<AiState, string> = {
  off: "○",
  no_key: "!",
  no_model: "!",
  ready: "●",
  ok: "●",
  error: "✕",
};

const CUSTOM = "__custom__";

export function AiStatusBar({ usage }: { usage: string }) {
  const [st, setSt] = useState<AiStatus | null>(null);
  const [test, setTest] = useState<AiTest | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const s = await getAiStatus();
      setSt(s);
      setTest(s.last_test);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : TEXT.loadFail);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function choose(provider: AiProvider, model: string) {
    setBusy(true);
    try {
      const s = await setAiChoice(provider, model);
      setSt(s);
      setTest(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : TEXT.loadFail);
    } finally {
      setBusy(false);
    }
  }

  async function onModel(value: string) {
    if (!st) return;
    if (value === CUSTOM) {
      const typed = window.prompt(TEXT.customPrompt, st.model)?.trim();
      if (typed) await choose(st.provider, typed);
      return;
    }
    await choose(st.provider, value);
  }

  async function onTest() {
    setBusy(true);
    try {
      setTest(await testAi());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : TEXT.loadFail);
    } finally {
      setBusy(false);
    }
  }

  const box = {
    display: "flex",
    flexWrap: "wrap" as const,
    alignItems: "center",
    gap: 10,
    padding: "10px 14px",
    margin: "0 0 16px",
    background: color.surface,
    border: `1px solid ${color.border}`,
    borderRadius: 12,
  };

  if (error && !st) {
    return (
      <div style={box}>
        <Badge tone="muted">{TEXT.ai}</Badge>
        <span style={{ color: color.danger, fontSize: 14 }}>{error}</span>
      </div>
    );
  }
  if (!st) return null;

  const models = st.models.includes(st.model) || !st.model ? st.models : [st.model, ...st.models];

  return (
    <div style={box} aria-label="AI 연결 상태">
      <strong style={{ color: color.info, fontSize: 14 }}>{TEXT.ai}</strong>
      <Badge tone={TONE[st.state]}>
        {DOT[st.state]} {st.state_label}
      </Badge>
      <span style={{ color: color.muted, fontSize: 13, flex: "1 1 160px", minWidth: 0 }}>{usage}</span>

      <label style={{ fontSize: 13, color: color.muted }}>
        {TEXT.provider}{" "}
        <select
          value={st.provider}
          disabled={busy}
          onChange={(e) => void choose(e.target.value as AiProvider, "")}
        >
          {st.providers.map((p) => (
            <option key={p} value={p}>
              {TEXT.providerLabel[p]}
            </option>
          ))}
        </select>
      </label>
      <label style={{ fontSize: 13, color: color.muted }}>
        {TEXT.model}{" "}
        <select value={st.model} disabled={busy} onChange={(e) => void onModel(e.target.value)}>
          {models.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
          <option value={CUSTOM}>{TEXT.custom}</option>
        </select>
      </label>
      <button type="button" className="primary" onClick={() => void onTest()} disabled={busy}>
        {busy ? TEXT.testing : TEXT.test}
      </button>

      {test && (
        <span
          style={{
            flexBasis: "100%",
            fontSize: 13,
            color: test.ok ? color.success : color.danger,
          }}
        >
          {test.ok ? "✔" : "✖"} {test.message} · {test.checked_at.replace("T", " ")}
          {test.ok && ` · ${test.elapsed_ms}ms`}
        </span>
      )}
    </div>
  );
}
