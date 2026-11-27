// B1-01~07 출처별 수집 상태와 업데이트 날짜 (LSH)
// 출처마다: 이름 · 상태 · 건수 · 마지막 수집 시각 · 가장 최근 원문 날짜. 자세한 메시지는 마우스를 올리면 보인다.
import { Badge } from "../../../components/ui/Badge";
import { color } from "../../../components/ui/tokens";
import type { Tone } from "../../../components/ui/tokens";
import type { SourceStatus as Row } from "../../../lib/types/b1";

const STATUS: Record<Row["status"], { text: string; tone: Tone }> = {
  ok: { text: "✔ 수집", tone: "success" },
  failed: { text: "✖ 수집 실패", tone: "danger" },
  manual: { text: "✋ 수동 업로드", tone: "warning" },
  off: { text: "사용 안 함", tone: "muted" },
  waiting: { text: "○ 대기", tone: "muted" },
};

const TEXT = {
  count: (n: number) => `${n}건`,
  collectedAt: (t: string) => `수집 ${t}`,
  latest: (d: string) => `최신 원문 ${d}`,
};

/** "2026-11-26T03:04:12+09:00" → "11/26 03:04" (서버가 KST로 저장한 글자를 그대로 자른다) */
function shortTime(iso: string): string {
  return `${iso.slice(5, 7)}/${iso.slice(8, 10)} ${iso.slice(11, 16)}`;
}

/** "2026-11-21" → "11/21" */
function shortDate(iso: string): string {
  return `${iso.slice(5, 7)}/${iso.slice(8, 10)}`;
}

export function SourceStatus({ rows, compact = false }: { rows: Row[]; compact?: boolean }) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: compact ? 6 : 8, margin: compact ? 0 : "8px 0 16px" }}>
      {rows.map((r) => {
        const dates = [
          r.status === "ok" ? TEXT.count(r.count) : "",
          r.at ? TEXT.collectedAt(shortTime(r.at)) : "",
          r.latest_posted_at ? TEXT.latest(shortDate(r.latest_posted_at)) : "",
        ].filter(Boolean);
        return (
          <span key={r.source} title={r.message} style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
            {compact ? <small>{r.name}</small> : r.name} <Badge tone={STATUS[r.status].tone}>{STATUS[r.status].text}</Badge>
            {dates.length > 0 && <small style={{ color: color.muted }}>{dates.join(" · ")}</small>}
          </span>
        );
      })}
    </div>
  );
}
