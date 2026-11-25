import { color } from "./tokens";

export function Loading({ message = "불러오는 중…" }: { message?: string }) {
  return <p style={{ color: color.muted, padding: 16 }}>{message}</p>;
}
