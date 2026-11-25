"use client";
// 법령 개정 (B1-12~14, LSH). DESIGN.md 6장.

import { useCallback, useEffect, useState } from "react";
import { ErrorState } from "../../components/ui/ErrorState";
import { Loading } from "../../components/ui/Loading";
import { RunGate } from "../../components/ui/RunGate";
import { color } from "../../components/ui/tokens";
import { fetchLaw, getLaw } from "../../lib/api/b1/law";
import type { LawFetchResult } from "../../lib/types/b1";
import type { LawChange, Run } from "../../lib/types/core";
import { LawDetail } from "./_components/LawDetail";
import { LawTable } from "./_components/LawTable";

const TEXT = {
  title: "법령 개정",
  fetch: "법령 개정 가져오기 (법제처 API · Supabase DB)",
  empty: "이번 보고 기간에 새로 시행된 관련 개정: 해당 없음",
};

function Body({ run }: { run: Run }) {
  const [rows, setRows] = useState<LawChange[] | null>(null);
  const [selected, setSelected] = useState<LawChange | null>(null);
  const [result, setResult] = useState<LawFetchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const r = await getLaw(run.id);
      setRows(r);
      setSelected((s) => (s ? r.find((x) => x.id === s.id) ?? null : null));
    } catch (e) {
      setError(e instanceof Error ? e.message : "불러오지 못했습니다");
    }
  }, [run.id]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onFetch() {
    setBusy(true);
    try {
      setResult(await fetchLaw(run.id));
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "가져오지 못했습니다");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button type="button" className="primary" onClick={onFetch} disabled={busy}>{busy ? "가져오는 중…" : TEXT.fetch}</button>
      {result && (
        <p style={{ color: color.muted }}>
          보고 기준: 시행일 {result.window_start} ~ {result.window_end} 새로 시행된 개정 (이미 보고한 개정 제외) · 찾은 {result.found}건 · 넣은 {result.added}건
        </p>
      )}
      {result?.errors.map((e) => (
        <ErrorState key={e} message={e} onRetry={onFetch} />
      ))}
      {error && <ErrorState message={error} onRetry={load} />}
      {rows === null && !error && <Loading />}
      {rows !== null && rows.length === 0 && <p style={{ padding: 16 }}>{TEXT.empty}</p>}
      {rows !== null && rows.length > 0 && (
        <div style={{ display: "flex", gap: 16, alignItems: "flex-start", marginTop: 12 }}>
          <div style={{ flex: 1 }}><LawTable rows={rows} onSelect={setSelected} /></div>
          {selected && <LawDetail law={selected} onSaved={load} />}
        </div>
      )}
    </>
  );
}

export default function LawPage() {
  return <RunGate title={TEXT.title}>{(run) => <Body run={run} />}</RunGate>;
}
