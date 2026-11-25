// 사람이 확인할 일 (C-06, KHS). 한 줄을 누르면 그 단계로 바로 간다 (DESIGN.md 3-1).
import Link from "next/link";
import { GROUPS } from "../../components/ui/steps";
import { color } from "../../components/ui/tokens";
import type { Todo } from "../../lib/types/core";

const TEXT = {
  title: "사람이 확인할 일",
  none: "이번 주 확인할 일이 모두 끝났어요.",
};

export function TodoList({ todos }: { todos: Todo[] }) {
  return (
    <section style={{ marginTop: 24 }}>
      <h2 className="section-label">{TEXT.title}</h2>
      {todos.length === 0 ? (
        <p style={{ color: color.muted }}>{TEXT.none}</p>
      ) : (
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {todos.map((t) => (
            <li key={t.key} style={{ marginBottom: 8 }}>
              <Link
                href={t.href}
                style={{
                  display: "flex",
                  gap: 10,
                  alignItems: "center",
                  padding: "10px 14px",
                  borderRadius: 10,
                  background: color.card,
                  border: "1px solid transparent",
                  color: color.text,
                  textDecoration: "none",
                }}
              >
                <span aria-hidden style={{ color: color.warning }}>⚠</span>
                <span>{t.text}</span>
                <span style={{ marginLeft: "auto", color: color.info, whiteSpace: "nowrap" }}>{GROUPS[t.group].name} ›</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
