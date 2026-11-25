"use client";
// 단계 바 (KHS, DESIGN.md 1-0). 순서대로 안내하지만 막지 않는다: 아무 단계나 눌러 이동할 수 있다.
// 상태·건수는 GET /api/core/runs/{run_id}/status (RunStatusContext)에서 읽는다.
import Link from "next/link";
import type { StepGroup, StepStatus } from "../../lib/types/core";
import { useRunStatus } from "./RunStatusContext";
import { stepsOf } from "./steps";
import { color } from "./tokens";

const TEXT = {
  done: "완료",
  viewing: "지금 보는 단계",
  notReady: "재료 준비가 아직 끝나지 않았어요. 지금까지의 재료로 만든 미리보기예요.",
  label: (group: StepGroup) => (group === "b1" ? "재료 준비 단계" : "보고서·메일 단계"),
};

export function StepBar({ group, current }: { group: StepGroup; current: string }) {
  const { state } = useRunStatus();
  const status = state.kind === "ok" ? state.status : null;
  const byKey = new Map<string, StepStatus>((status?.steps ?? []).map((s) => [s.key, s]));
  const showNotReady = group === "b2" && status !== null && !status.materials_ready;

  return (
    <div style={{ marginBottom: 20 }}>
      {showNotReady && (
        <p
          role="status"
          style={{ margin: "0 0 10px", padding: "10px 14px", borderRadius: 10, background: "#fff4e5", color: color.warning, fontWeight: 600 }}
        >
          ⚠ {TEXT.notReady}
        </p>
      )}
      <nav aria-label={TEXT.label(group)}>
        <ol style={{ display: "flex", gap: 8, listStyle: "none", margin: 0, padding: 0, flexWrap: "wrap" }}>
          {stepsOf(group).map((def, i) => {
            const st = byKey.get(def.key);
            const done = st?.done ?? false;
            const viewing = def.key === current;
            const border = viewing ? color.primary : done ? color.success : "transparent";
            return (
              <li key={def.key} style={{ flex: "1 1 140px", minWidth: 130 }}>
                <Link
                  href={def.href}
                  aria-current={viewing ? "step" : undefined}
                  style={{
                    display: "flex",
                    gap: 10,
                    alignItems: "center",
                    padding: "8px 12px",
                    borderRadius: 14,
                    textDecoration: "none",
                    color: color.text,
                    background: viewing ? color.primarySoft : color.card,
                    border: `${viewing ? 2 : 1}px solid ${border}`,
                  }}
                >
                  <span
                    aria-hidden
                    style={{
                      width: 26,
                      height: 26,
                      flexShrink: 0,
                      borderRadius: 999,
                      display: "grid",
                      placeItems: "center",
                      fontSize: 13,
                      fontWeight: 800,
                      color: done || viewing ? "#fff" : color.muted,
                      background: done ? color.success : viewing ? color.primary : "#e6edf4",
                    }}
                  >
                    {done ? "✓" : i + 1}
                  </span>
                  <span style={{ minWidth: 0 }}>
                    <span style={{ display: "block", fontWeight: viewing ? 800 : 600, fontSize: 14 }}>{def.name}</span>
                    <span style={{ display: "block", fontSize: 12, color: done ? color.success : color.muted }}>
                      {done ? `${TEXT.done}${st?.note ? ` · ${st.note}` : ""}` : st?.note || (viewing ? TEXT.viewing : " ")}
                    </span>
                  </span>
                </Link>
              </li>
            );
          })}
        </ol>
      </nav>
    </div>
  );
}
