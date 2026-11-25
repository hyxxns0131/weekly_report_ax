// 이번 주 현황 머리글 (C-06, KHS)
import type { Run } from "../../lib/types/core";

function mmdd(iso: string): string {
  const [, m, d] = iso.split("-");
  return `${m}/${d}`;
}

export function RunHeader({ run, onCreate, busy }: { run: Run | null; onCreate: () => void; busy: boolean }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 16 }}>
      <h1 style={{ margin: 0, fontSize: 22 }}>주간 검역 보고서</h1>
      {run && (
        <span>
          {run.week_label} ({mmdd(run.period_start)} 월 ~ {mmdd(run.period_end)} 일)
        </span>
      )}
      <button type="button" className="primary" onClick={onCreate} disabled={busy} style={{ marginLeft: "auto" }}>
        주간 실행 만들기
      </button>
    </div>
  );
}
