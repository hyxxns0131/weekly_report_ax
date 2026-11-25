// B1-14 대조 배지 (LSH)
import { Badge } from "../../../components/ui/Badge";
import type { Crosscheck } from "../../../lib/types/core";

export function CrosscheckBadge({ value }: { value: Crosscheck }) {
  if (value === "match") return <Badge tone="success">✔ 일치</Badge>;
  if (value === "api_only") return <Badge tone="danger">⚠ API만</Badge>;
  if (value === "notice_only") return <Badge tone="danger">⚠ 공문만</Badge>;
  return <Badge tone="muted">○ 대조 안 함</Badge>;
}
