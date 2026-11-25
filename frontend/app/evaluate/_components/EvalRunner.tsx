"use client";
// B2-06 검증 실행 (KHW)
import { useEffect, useState } from "react";
import { EmptyState } from "../../../components/ui/EmptyState";
import { getGoldenWeeks, runEval } from "../../../lib/api/b2/evaluate";
import type { EvalResult } from "../../../lib/types/core";

export function EvalRunner({ runId, onResult }: { runId: number; onResult: (r: EvalResult) => void }) {
  const [weeks, setWeeks] = useState<string[] | null>(null);
  const [week, setWeek] = useState("");
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    getGoldenWeeks().then((w) => { setWeeks(w); setWeek(w[0] ?? ""); }).catch(() => setWeeks([]));
  }, []);
  if (weeks !== null && weeks.length === 0)
    return <EmptyState message="과거 보고서 정답 자료가 없습니다(SAMC 전달 대기). samples/past_reports/ 에 비식별 정답 JSON을 넣으면 검증할 수 있습니다." />;
  return (
    <div style={{ marginBottom: 16 }}>
      비교할 과거 보고서:{" "}
      <select value={week} onChange={(e) => setWeek(e.target.value)}>
        {(weeks ?? []).map((w) => <option key={w} value={w}>{w}</option>)}
      </select>{" "}
      <button type="button" disabled={!week} onClick={async () => {
        try { onResult(await runEval(runId, week)); setError(null); } catch (e) { setError(e instanceof Error ? e.message : "실패"); }
      }}>검증 실행</button>
      {error && <p>✖ {error}</p>}
    </div>
  );
}
