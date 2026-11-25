// B1-11 고객사별 보기 (LSH). 그대로 고객사 메일 내용이 된다.
import { color } from "../../../components/ui/tokens";
import type { MatchRow } from "../../../lib/types/b1";
import { isOn } from "./MatchByItem";

export function MatchByCustomer({ rows }: { rows: MatchRow[] }) {
  const groups = new Map<string, MatchRow[]>();
  for (const m of rows.filter(isOn)) {
    const key = `${m.customer_name} (${m.customer_id})`;
    groups.set(key, [...(groups.get(key) ?? []), m]);
  }
  if (groups.size === 0) return <p style={{ color: color.muted }}>관련 고객사가 없습니다.</p>;
  return (
    <div>
      {[...groups.entries()].map(([name, list]) => (
        <section key={name} style={{ background: color.surface, border: `1px solid ${color.border}`, padding: 12, marginBottom: 12 }}>
          <strong>{name}</strong> · 관련 {list.length}건
          <ul>
            {list.map((m) => (
              <li key={m.item_id}>
                {m.item_title} — <span style={{ color: color.muted }}>{m.reason}</span>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
