// 선별 결과 배지 (KHS 공통). 글자 + 색, AI/확인 표시 (DESIGN.md 4·11장)
import type { Selection } from "../../lib/types/core";
import { Badge } from "./Badge";
import type { Tone } from "./tokens";

const LABEL: Record<string, { text: string; tone: Tone }> = {
  relevant: { text: "관련", tone: "success" },
  irrelevant: { text: "무관", tone: "muted" },
  review_needed: { text: "검토 필요", tone: "warning" },
};

export function LabelBadge({ selection }: { selection: Selection | null }) {
  if (!selection) return <Badge tone="muted">분석 전</Badge>;
  const label = selection.final_label ?? selection.ai_label;
  const l = LABEL[label];
  return (
    <span style={{ display: "inline-flex", gap: 4 }}>
      <Badge tone={l.tone}>{l.text}</Badge>
      {selection.final_label ? <Badge tone="muted">확인</Badge> : <Badge tone="info">AI</Badge>}
    </span>
  );
}

export const CATEGORY_TEXT: Record<string, string> = {
  unfit: "부적합",
  inspection_order: "통관단계 검사지시",
  law_change: "법령",
  policy_news: "정책소식",
  other: "기타",
};
