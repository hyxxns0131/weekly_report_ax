"use client";
// ? 아이콘 + 작은 말풍선 (LSH, /collect 데모 뷰). 마우스를 올리거나 키보드로 포커스하면 뜬다.
import { useId, useState } from "react";
import { color, space } from "../../../components/ui/tokens";

const TEXT = { label: "이유 보기" };

export function HelpTip({ lines }: { lines: string[] }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  if (lines.length === 0) return null;
  return (
    <span
      style={{ position: "relative", display: "inline-block" }}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        aria-label={TEXT.label}
        aria-describedby={open ? id : undefined}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onKeyDown={(e) => {
          if (e.key === "Escape") setOpen(false);
        }}
        style={{
          width: 22,
          height: 22,
          padding: 0,
          borderRadius: 999,
          border: `1px solid ${color.border}`,
          background: color.primarySoft,
          color: color.info,
          fontWeight: 700,
          cursor: "help",
          lineHeight: 1,
        }}
      >
        ?
      </button>
      {open && (
        <span
          id={id}
          role="tooltip"
          style={{
            position: "absolute",
            right: 0,
            top: "calc(100% + 4px)",
            zIndex: 10,
            width: 320,
            padding: space.sm,
            background: color.surface,
            color: color.text,
            border: `1px solid ${color.border}`,
            borderRadius: 6,
            boxShadow: `0 2px 8px ${color.border}`,
            textAlign: "left",
            whiteSpace: "normal",
          }}
        >
          {lines.map((l, i) => (
            <small key={i} style={{ display: "block", lineHeight: 1.5 }}>
              {l}
            </small>
          ))}
        </span>
      )}
    </span>
  );
}
