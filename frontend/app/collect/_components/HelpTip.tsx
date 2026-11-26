"use client";
// ? 아이콘 + 말풍선 (LSH, /collect 데모 뷰). 마우스를 올리거나 키보드로 포커스하면 뜬다.
// 말풍선은 body 바로 아래(포털)에 position: fixed로 그린다. 그래서 스크롤 상자·카드의 overflow에 잘리지 않는다.
// 아래 공간이 모자라면 버튼 위로 뒤집고, 화면 오른쪽 밖으로 나가지 않게 가장자리에 붙인다.
import { useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { color, space } from "../../../components/ui/tokens";

const TEXT = { label: "이유 보기" };
const WIDTH = 320;
const GAP = 4;
const EDGE = 8;

type Pos = { top: number; left: number };

export function HelpTip({ lines }: { lines: string[] }) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState<Pos | null>(null);
  const btnRef = useRef<HTMLButtonElement>(null);
  const tipRef = useRef<HTMLSpanElement>(null);
  const id = useId();

  // 열릴 때와 화면이 움직일 때 위치를 다시 잰다.
  useLayoutEffect(() => {
    if (!open) return;
    const place = () => {
      const btn = btnRef.current;
      if (!btn) return;
      const r = btn.getBoundingClientRect();
      const h = tipRef.current?.offsetHeight ?? 0;
      const below = r.bottom + GAP;
      const flip = h > 0 && below + h > window.innerHeight - EDGE && r.top - GAP - h >= EDGE;
      const top = flip ? r.top - GAP - h : below;
      const maxLeft = window.innerWidth - WIDTH - EDGE;
      const left = Math.max(EDGE, Math.min(r.right - WIDTH, maxLeft));
      setPos({ top, left });
    };
    place();
    window.addEventListener("scroll", place, true);
    window.addEventListener("resize", place);
    return () => {
      window.removeEventListener("scroll", place, true);
      window.removeEventListener("resize", place);
    };
  }, [open]);

  if (lines.length === 0) return null;

  const tip =
    open && typeof document !== "undefined"
      ? createPortal(
          <span
            ref={tipRef}
            id={id}
            role="tooltip"
            style={{
              position: "fixed",
              top: pos?.top ?? 0,
              left: pos?.left ?? 0,
              visibility: pos ? "visible" : "hidden",
              zIndex: 1000,
              width: WIDTH,
              maxWidth: `calc(100vw - ${EDGE * 2}px)`,
              padding: space.sm,
              background: color.surface,
              color: color.text,
              border: `1px solid ${color.border}`,
              borderRadius: 6,
              boxShadow: `0 2px 8px ${color.border}`,
              textAlign: "left",
              whiteSpace: "normal",
              pointerEvents: "none",
              display: "block",
            }}
          >
            {lines.map((l, i) => (
              <small key={i} style={{ display: "block", lineHeight: 1.5, marginTop: i > 0 ? 4 : 0 }}>
                {l}
              </small>
            ))}
          </span>,
          document.body,
        )
      : null;

  return (
    <span
      style={{ display: "inline-block" }}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        ref={btnRef}
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
      {tip}
    </span>
  );
}
