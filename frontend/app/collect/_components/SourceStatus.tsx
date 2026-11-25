// B1-01~07 출처별 수집 상태 (LSH)
import { Badge } from "../../../components/ui/Badge";
import type { Tone } from "../../../components/ui/tokens";
import type { SourceStatus as Row } from "../../../lib/types/b1";

const STATUS: Record<Row["status"], { text: string; tone: Tone }> = {
  ok: { text: "✔ 수집", tone: "success" },
  failed: { text: "✖ 수집 실패", tone: "danger" },
  manual: { text: "✋ 수동 업로드", tone: "warning" },
  off: { text: "사용 안 함", tone: "muted" },
  waiting: { text: "○ 대기", tone: "muted" },
};

export function SourceStatus({ rows }: { rows: Row[] }) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, margin: "8px 0 16px" }}>
      {rows.map((r) => (
        <span key={r.source} title={r.message}>
          {r.name} <Badge tone={STATUS[r.status].tone}>{STATUS[r.status].text}</Badge>
          {r.status === "ok" && ` ${r.count}건`}
        </span>
      ))}
    </div>
  );
}
