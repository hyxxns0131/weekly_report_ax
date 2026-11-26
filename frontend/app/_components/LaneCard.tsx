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

  return (
    <section
      aria-label={g.name}
      style={{ flex: "1 1 360px", background: color.card, borderRadius: 20, padding: 22 }}
    >
      <h2 style={{ margin: "0 0 12px", fontSize: 17 }}>
        {g.name} <span style={{ color: color.muted, fontWeight: 500, fontSize: 14 }}>({g.owner})</span>
      </h2>
      <ul style={{ display: "flex", flexWrap: "wrap", gap: "6px 14px", listStyle: "none", margin: 0, padding: 0 }}>
        {stepsOf(group).map((def) => {
          const st = byKey.get(def.key)?.state ?? "waiting";
          const tone = st === "done" ? color.success : st === "current" ? color.primary : color.muted;
          return (
            <li key={def.key}>
              <Link href={def.href} style={{ color: tone, textDecoration: "none", fontWeight: st === "current" ? 800 : 500 }}>
                <span aria-hidden>{MARK[st]}</span>
                <span className="sr-only">{MARK_LABEL[st]} </span>
                {def.name}
              </Link>
            </li>
          );
        })}
      </ul>
      {group === "b1" && status.counts.collect_failed > 0 && (
        <p style={{ margin: "10px 0 0", color: color.danger, fontSize: 14 }}>
          ✖ <Link href="/collect/">{TEXT.failed(status.counts.collect_failed)}</Link>
        </p>
      )}
      <div style={{ display: "flex", alignItems: "center", marginTop: 14 }}>
        <span style={{ fontWeight: 700 }}>{nowText}</span>
        <Link href={stepHref(currentKey, group)} className="button-link" style={{ marginLeft: "auto" }}>
          {TEXT.resume}
        </Link>
      </div>
    </section>
  );
}
