// 보드 카드 공통 틀 (LSH, /collect). 위 작은 꼬리표 → 제목 줄 → 내용 → 아래 상태 줄.
// 색은 components/ui/tokens.ts만 쓴다.
import type { CSSProperties, ReactNode } from "react";
import { color, space } from "../../../components/ui/tokens";

export const CARD_WIDTH = 360;
export const CARD_HEIGHT = 230;

export function BoardCard({
  tag,
  icon,
  title,
  help,
  footer,
  children,
  style,
}: {
  tag: string;
  icon: string;
  title: string;
  help?: ReactNode;
  footer?: ReactNode;
  children: ReactNode;
  style?: CSSProperties;
}) {
  return (
    <article style={{ position: "relative", paddingTop: 14, ...style }}>
      <span
        style={{
          position: "absolute",
          top: 0,
          left: 12,
          padding: "1px 8px",
          borderRadius: 6,
          background: color.primarySoft,
          border: `1px solid ${color.border}`,
          color: color.info,
          fontWeight: 700,
        }}
      >
        <small>{tag}</small>
      </span>
      <div
        style={{
          height: "100%",
          display: "flex",
          flexDirection: "column",
          gap: space.sm,
          padding: `${space.md}px ${space.md}px ${space.sm}px`,
          background: color.surface,
          border: `1px solid ${color.border}`,
          borderRadius: 12,
          boxShadow: `0 1px 3px ${color.border}`,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: space.sm }}>
          <span aria-hidden>{icon}</span>
          <strong style={{ flex: 1 }}>{title}</strong>
          {help}
        </div>
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: space.sm, minHeight: 0 }}>
          {children}
        </div>
        {footer && (
          <div style={{ color: color.muted, borderTop: `1px solid ${color.border}`, paddingTop: space.xs }}>
            <small>{footer}</small>
          </div>
        )}
      </div>
    </article>
  );
}

/** 카드 안 회색 상자 (사진의 URL·본문 칸 모양). */
export function InnerBox({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div
      style={{
        padding: `${space.xs}px ${space.sm}px`,
        background: color.background,
        border: `1px solid ${color.border}`,
        borderRadius: 8,
        ...style,
      }}
    >
      {children}
    </div>
  );
}
