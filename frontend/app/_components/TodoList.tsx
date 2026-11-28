// 사람이 확인할 일 (C-06, KHS). 한 줄을 누르면 그 단계로 바로 간다 (DESIGN.md 3-1).
import Link from "next/link";
import { GROUPS } from "../../components/ui/steps";
import { color } from "../../components/ui/tokens";
import type { Todo } from "../../lib/types/core";

const TEXT = {
  title: "사람이 확인할 일",
  none: "이번 주 확인할 일이 모두 끝났어요.",
};

const TAG: Record<Todo["group"], { fg: string; bg: string }> = {
  b1: { fg: color.info, bg: color.primarySoft },
  b2: { fg: color.success, bg: "#e8f5ec" },
};

export function TodoList({ todos }: { todos: Todo[] }) {
  return (
    <section className="white-card" style={{ marginTop: 20, padding: "20px 24px" }}>
      <h2 style={{ display: "flex", alignItems: "center", gap: 8, margin: "0 0 10px", fontSize: 16 }}>
        {TEXT.title}
        {todos.length > 0 && (
          <span style={{ fontSize: 12, fontWeight: 800, color: "#fff", background: color.primary, padding: "0 9px", borderRadius: 999 }}>{todos.length}</span>
        )}
      </h2>
      {todos.length === 0 ? (
        <p style={{ color: color.muted, margin: 0 }}>{TEXT.none}</p>
      ) : (
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {todos.map((t, i) => (
            <li key={t.key} style={{ borderTop: i === 0 ? "none" : `1px solid ${color.border}` }}>
              <Link
                href={t.href}
                style={{
                  display: "flex",
                  gap: 12,
                  alignItems: "center",
                  padding: "12px 4px",
                  color: color.text,
                  textDecoration: "none",
                }}
              >
                <span
                  style={{ fontSize: 12, fontWeight: 700, color: TAG[t.group].fg, background: TAG[t.group].bg, padding: "2px 10px", borderRadius: 6, whiteSpace: "nowrap" }}
                >
                  {GROUPS[t.group].name}
                </span>
                <span aria-hidden style={{ color: color.warning }}>⚠</span>
                <span>{t.text}</span>
                <span aria-hidden style={{ marginLeft: "auto", color: color.info, fontWeight: 700 }}>›</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
