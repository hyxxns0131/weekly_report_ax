"use client";
// 연결 설정 (C-01, KHS). 외부 연결마다 상태 + [연결 검사]. AI는 회사·모델도 고른다.
// 키·토큰 값은 화면에 오지 않는다(.env에만 있음).

import { useCallback, useEffect, useState } from "react";
import { AiStatusBar } from "../../components/ui/AiStatusBar";
import { Badge } from "../../components/ui/Badge";
import { ErrorState } from "../../components/ui/ErrorState";
import { Loading } from "../../components/ui/Loading";
import { color, type Tone } from "../../components/ui/tokens";
import { getConnections, testConnection } from "../../lib/api/core";
import type { ConnId, ConnState, ConnStatus } from "../../lib/types/core";

const TEXT = {
  title: "연결 설정",
  intro:
    "프로그램이 쓰는 외부 연결을 한곳에서 확인합니다. 키는 .env에만 넣고, 넣은 뒤에는 [연결 검사]를 눌러 다시 확인하세요. 검사는 읽기만 하고 토큰을 쓰지 않습니다.",
  aiUsage: "선별·정보 추출·법령 요지 요약·메일 초안에 씁니다. 가벼운 작업은 낮은 모델로 토큰을 아낄 수 있습니다",
  test: "연결 검사",
  testing: "검사 중…",
  env: ".env 변수",
  never: "아직 검사하지 않았습니다",
  loadFail: "연결 상태를 불러오지 못했습니다",
};

const TONE: Record<ConnState, Tone> = {
  off: "muted",
  no_key: "warning",
  ready: "info",
  ok: "success",
  error: "danger",
};

const DOT: Record<ConnState, string> = { off: "○", no_key: "!", ready: "●", ok: "●", error: "✕" };

function ConnCard({ c, onChanged }: { c: ConnStatus; onChanged: (c: ConnStatus) => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onTest() {
    setBusy(true);
    try {
      onChanged(await testConnection(c.id));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : TEXT.loadFail);
    } finally {
      setBusy(false);
    }
  }

  const t = c.last_test;
  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        gap: 10,
        padding: "12px 14px",
        marginBottom: 10,
        background: color.card,
        border: "1px solid transparent",
        borderRadius: 12,
      }}
    >
      <strong style={{ minWidth: 170 }}>{c.name}</strong>
      <Badge tone={TONE[c.state]}>
        {DOT[c.state]} {c.state_label}
      </Badge>
      <span style={{ color: color.muted, fontSize: 13, flex: "1 1 200px", minWidth: 0 }}>{c.usage}</span>
      <button type="button" className="primary" onClick={() => void onTest()} disabled={busy}>
        {busy ? TEXT.testing : TEXT.test}
      </button>
      <span style={{ flexBasis: "100%", fontSize: 12, color: color.muted }}>
        {TEXT.env}: {c.env_names.join(", ")}
      </span>
      {c.hint && <span style={{ flexBasis: "100%", fontSize: 13, color: color.warning }}>! {c.hint}</span>}
      <span style={{ flexBasis: "100%", fontSize: 13, color: t ? (t.ok ? color.success : color.danger) : color.muted }}>
        {t ? `${t.ok ? "✔" : "✖"} ${t.message} · ${t.checked_at}${t.ok ? ` · ${t.elapsed_ms}ms` : ""}` : TEXT.never}
      </span>
      {error && <span style={{ flexBasis: "100%", fontSize: 13, color: color.danger }}>{error}</span>}
    </div>
  );
}

export default function ConnectionsPage() {
  const [rows, setRows] = useState<ConnStatus[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setRows(await getConnections());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : TEXT.loadFail);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  function replace(c: ConnStatus) {
    setRows((rs) => (rs ? rs.map((r) => (r.id === c.id ? c : r)) : rs));
  }

  const others = rows?.filter((r) => r.id !== ("ai" satisfies ConnId)) ?? [];

  return (
    <>
      <h1 style={{ fontSize: 22 }}>{TEXT.title}</h1>
      <p style={{ color: color.muted, marginTop: -4 }}>{TEXT.intro}</p>
      <AiStatusBar usage={TEXT.aiUsage} />
      {error && <ErrorState message={error} onRetry={load} />}
      {!error && rows === null && <Loading />}
      {others.map((c) => (
        <ConnCard key={c.id} c={c} onChanged={replace} />
      ))}
    </>
  );
}
