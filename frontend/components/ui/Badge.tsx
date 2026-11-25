import type { ReactNode } from "react";
import { color, type Tone } from "./tokens";

const SOFT: Record<Tone, string> = {
  danger: "#fdecec",
  warning: "#fff4e5",
  muted: "#eef2f6",
  info: "#e3f2fd",
  success: "#e8f5ec",
};

export function Badge({ tone, children }: { tone: Tone; children: ReactNode }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: 999,
        border: `1px solid ${color[tone]}33`,
        background: SOFT[tone],
        color: color[tone],
        fontSize: 12,
        fontWeight: 700,
        whiteSpace: "nowrap",
        lineHeight: 1.6,
      }}
    >
      {children}
    </span>
  );
}

export function AiBadge() {
  return <Badge tone="info">AI 결과 · 담당자 확인 전</Badge>;
}
