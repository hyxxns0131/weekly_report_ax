"use client";
// 수집·선별 (B1-01~09, LSH). DESIGN.md 4장.

import { useCallback, useEffect, useState } from "react";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorState } from "../../components/ui/ErrorState";
import { Loading } from "../../components/ui/Loading";
import { AiStatusBar } from "../../components/ui/AiStatusBar";
import { RunGate } from "../../components/ui/RunGate";
import { color } from "../../components/ui/tokens";
import { analyze } from "../../lib/api/b1/classify";
import { collect, getItems, getSourceStatus } from "../../lib/api/b1/collect";
import type { ItemRow, SourceStatus as SourceRow } from "../../lib/types/b1";
import type { Run } from "../../lib/types/core";
import { ClassifyTable } from "./_components/ClassifyTable";
import { ExtractPanel } from "./_components/ExtractPanel";
import { SourceStatus } from "./_components/SourceStatus";
import { UploadPanel } from "./_components/UploadPanel";

const TEXT = {
  title: "수집·선별",
  collect: "자동 수집 (Supabase DB 포함)",
  analyze: "분석 실행",
  empty: "이번 주 자료가 없습니다. 위에서 자료를 올리거나 [자동 수집]을 눌러 주세요.",
  filters: [
    ["all", "전체"],
    ["relevant", "관련"],
    ["review_needed", "검토 필요"],
    ["irrelevant", "무관"],
  ] as const,
};

function CollectBody({ run }: { run: Run }) {
  const [rows, setRows] = useState<ItemRow[] | null>(null);
  const [sources, setSources] = useState<SourceRow[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [selected, setSelected] = useState<ItemRow | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [items, src] = await Promise.all([getItems(run.id, filter), getSourceStatus(run.id)]);
      setRows(items);
      setSources(src);
      setSelected((s) => (s ? items.find((i) => i.raw.id === s.raw.id) ?? null : null));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "불러오지 못했습니다");
    }
  }, [run.id, filter]);

  useEffect(() => {
    void load();
  }, [load]);

  async function act(fn: () => Promise<string>) {
    setBusy(true);
    try {
      setMsg(await fn());
      await load();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "실패");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <UploadPanel runId={run.id} onDone={(m) => { setMsg(m); void load(); }} />
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <button type="button" disabled={busy} onClick={() => act(async () => {
          const r = await collect(run.id);
          return r.map((x) => `${x.source}: ${x.message || x.status}`).join(" · ");
        })}>
          {TEXT.collect}
        </button>
        <button type="button" className="primary" disabled={busy} onClick={() => act(async () => {
          const r = await analyze(run.id);
          return `분석 완료: 전체 ${r.total} · 관련 ${r.relevant} · 검토 필요 ${r.review_needed} · 무관 ${r.irrelevant} · 고객사 판단 ${r.matches}건`;
        })}>
          {TEXT.analyze}
        </button>
        <span style={{ marginLeft: "auto" }}>
          필터:{" "}
          {TEXT.filters.map(([v, l]) => (
            <button key={v} type="button" onClick={() => setFilter(v)} className={filter === v ? "primary" : undefined}>
              {l}
            </button>
          ))}
        </span>
      </div>
      {msg && <p style={{ color: color.muted }}>{msg}</p>}
      <SourceStatus rows={sources} />
      {error && <ErrorState message={error} onRetry={load} />}
      {!error && rows === null && <Loading />}
      {!error && rows !== null && rows.length === 0 && <EmptyState message={TEXT.empty} />}
      {!error && rows !== null && rows.length > 0 && (
        <div style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
          <div style={{ flex: 1 }}>
            <ClassifyTable rows={rows} onSelect={setSelected} selectedId={selected?.raw.id ?? null} />
          </div>
          {selected && <ExtractPanel row={selected} onChanged={load} />}
        </div>
      )}
    </>
  );
}

export default function CollectPage() {
  return <RunGate title={TEXT.title} aside={<AiStatusBar usage="선별(관련·무관·검토 필요)과 본문형 자료 정보 추출에 씁니다" />}>
      {(run) => <CollectBody run={run} />}
    </RunGate>;
}
