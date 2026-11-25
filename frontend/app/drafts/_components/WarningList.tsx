// B2-02~04 경고 (KHW): 출처 누락 · 다른 고객사명 · 원문에 없는 숫자
import { color } from "../../../components/ui/tokens";

export function WarningList({ warnings }: { warnings: string[] }) {
  if (warnings.length === 0) return <p style={{ color: color.success }}>✔ 경고 없음</p>;
  return (
    <ul style={{ color: color.warning }}>
      {warnings.map((w) => <li key={w}>⚠ {w}</li>)}
    </ul>
  );
}
