// 이번 주 현황 진행 칸 (C-06, KHS). 단계 점(✓ 끝, ● 지금, ○ 대기) + "지금: X" + [이어서 하기] (DESIGN.md 3-1).
import Link from "next/link";
import { GROUPS, stepHref, stepsOf } from "../../components/ui/steps";
import { color } from "../../components/ui/tokens";
import type { RunStatus, StepGroup } from "../../lib/types/core";

const TEXT = {
  now: "지금",
  allDone: "모든 단계 완료",
  waiting: "자료를 기다리는 중",
  resume: "이어서 하기",
  failed: (n: number) => `수집 실패 ${n}곳 → 직접 올리기`,
};

const MARK = { done: "✓", current: "●", waiting: "○" } as const;
const MARK_LABEL = { done: "완료", current: "진행·확인 중", waiting: "대기" } as const;

export function LaneCard({ group, status }: { group: StepGroup; status: RunStatus }) {
  const g = GROUPS[group];
  const byKey = new Map(status.steps.map((s) => [s.key, s]));
  const currentKey = status.current[group];
  const currentName = stepsOf(group).find((s) => s.key === currentKey)?.name;
  const waitingForMaterials = group === "b2" && !status.materials_ready && currentKey === "report";
  const nowText = currentKey === null ? TEXT.allDone : waitingForMaterials ? TEXT.waiting : `${TEXT.now}: ${currentName}`;

  const nowColor = currentKey === null ? color.success : waitingForMaterials ? color.muted : color.primary;

  return (
    <section aria-label={g.name} className="white-card" style={{ flex: "1 1 380px", padding: "22px 24px" }}>
      <h2 style={{ display: "flex", alignItems: "center", gap: 8, margin: "0 0 6px", fontSize: 16 }}>
        {g.name}
        <span style={{ color: color.info, background: color.primarySoft, fontWeight: 700, fontSize: 12, padding: "1px 9px", borderRadius: 999 }}>
          {g.owner}
        </span>
      </h2>
      <p style={{ margin: "0 0 16px", fontSize: 24, fontWeight: 800, color: nowColor, letterSpacing: "-0.02em" }}>{nowText}</p>
      <ul style={{ display: "flex", flexWrap: "wrap", gap: 10, listStyle: "none", margin: 0, padding: 0 }}>
        {stepsOf(group).map((def) => {
          const st = byKey.get(def.key)?.state ?? "waiting";
          const tone = st === "done" ? color.success : st === "current" ? color.primary : color.muted;
          const tile = st === "done" ? "#e8f5ec" : st === "current" ? color.primary : "#eef2f7";
          return (
            <li key={def.key} style={{ flex: "0 0 86px" }}>
              <Link
                href={def.href}
                style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6, color: tone, textDecoration: "none", fontWeight: st === "current" ? 800 : 600, fontSize: 13, textAlign: "center" }}
              >
                <span
                  aria-hidden
                  style={{
                    width: 46,
                    height: 46,
                    borderRadius: 14,
                    display: "grid",
                    placeItems: "center",
                    fontSize: 18,
                    color: st === "current" ? "#fff" : tone,
                    background: tile,
                    boxShadow: st === "current" ? "0 6px 14px rgba(38, 114, 222, 0.3)" : "none",
                  }}
                >
                  {MARK[st]}
                </span>
                <span className="sr-only">{MARK_LABEL[st]} </span>
                <span style={{ wordBreak: "keep-all", lineHeight: 1.3 }}>{def.name}</span>
              </Link>
            </li>
          );
        })}
      </ul>
      {group === "b1" && status.counts.collect_failed > 0 && (
        <p style={{ margin: "14px 0 0", color: color.danger, fontSize: 14 }}>
          ✖ <Link href="/collect/">{TEXT.failed(status.counts.collect_failed)}</Link>
        </p>
      )}
      <div style={{ display: "flex", alignItems: "center", marginTop: 18, paddingTop: 14, borderTop: `1px solid ${color.border}` }}>
        <Link href={stepHref(currentKey, group)} className="button-link" style={{ marginLeft: "auto" }}>
          {TEXT.resume}
        </Link>
      </div>
    </section>
  );
}
