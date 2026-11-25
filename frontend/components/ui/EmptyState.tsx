import type { ReactNode } from "react";
import { color } from "./tokens";

export function EmptyState({ message, action }: { message: string; action?: ReactNode }) {
  return (
    <div style={{ padding: 32, textAlign: "center", color: color.muted }}>
      <p>{message}</p>
      {action}
    </div>
  );
}
