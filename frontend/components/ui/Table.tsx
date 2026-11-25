import type { ReactNode } from "react";
import { color } from "./tokens";

export type Column<T> = { key: string; header: string; render: (row: T) => ReactNode };

export function Table<T>({
  columns,
  rows,
  rowKey,
}: {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string;
}) {
  const cell = { padding: "10px 14px", borderBottom: `1px solid ${color.border}`, textAlign: "left" as const };
  return (
    <table style={{ width: "100%", borderCollapse: "collapse", background: color.surface }}>
      <thead>
        <tr>
          {columns.map((c) => (
            <th key={c.key} style={{ ...cell, fontWeight: 600 }}>
              {c.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={rowKey(r)}>
            {columns.map((c) => (
              <td key={c.key} style={cell}>
                {c.render(r)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
