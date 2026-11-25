// B2-01 보고서 미리보기 (KHW)
import { color } from "../../../components/ui/tokens";
import type { ReportOut } from "../../../lib/types/b2";

export function ReportPreview({ report }: { report: ReportOut }) {
  return (
    <section style={{ background: color.surface, border: `1px solid ${color.border}`, padding: 12, marginBottom: 16 }}>
      <strong>주간 보고서 · {report.report.week_label}</strong>
      <span style={{ color: color.muted, marginLeft: 8 }}>검토 필요 {report.review_needed}건</span>
      <pre style={{ whiteSpace: "pre-wrap", fontSize: 13 }}>{report.text}</pre>
    </section>
  );
}
