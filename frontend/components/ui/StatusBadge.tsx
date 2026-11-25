import { Badge } from "./Badge";
import type { Tone } from "./tokens";
import type { StageState } from "../../lib/types/core";

const STATE: Record<StageState, { icon: string; text: string; tone: Tone }> = {
  waiting: { icon: "○", text: "대기", tone: "muted" },
  in_progress: { icon: "●", text: "진행·확인 중", tone: "warning" },
  done: { icon: "✔", text: "완료", tone: "success" },
  failed: { icon: "✖", text: "실패", tone: "danger" },
};

export function StatusBadge({ state }: { state: StageState }) {
  const s = STATE[state];
  return (
    <Badge tone={s.tone}>
      {s.icon} {s.text}
    </Badge>
  );
}
