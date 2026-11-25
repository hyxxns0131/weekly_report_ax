// B1-12·13 법령 개정 목록 (LSH). 없는 값은 "확인 필요".
import { AiBadge } from "../../../components/ui/Badge";
import { type Column, Table } from "../../../components/ui/Table";
import type { LawChange } from "../../../lib/types/core";
import { CrosscheckBadge } from "./CrosscheckBadge";

const v = (x: string | null) => x ?? "확인 필요";

export function LawTable({ rows, onSelect }: { rows: LawChange[]; onSelect: (l: LawChange) => void }) {
  const columns: Column<LawChange>[] = [
    { key: "name", header: "법령·고시명", render: (l) => <button type="button" onClick={() => onSelect(l)} style={{ background: "none", border: "none", padding: 0, cursor: "pointer", textAlign: "left" }}>「{v(l.law_name)}」</button> },
    { key: "type", header: "구분", render: (l) => v(l.change_type) },
    { key: "no", header: "번호", render: (l) => v(l.number) },
    { key: "eff", header: "시행일", render: (l) => v(l.effective_at) },
    { key: "sum", header: "개정 요지", render: (l) => (l.final_summary ? l.final_summary : <>{v(l.ai_summary)} {l.ai_summary && <AiBadge />}</>) },
    { key: "cc", header: "대조", render: (l) => <CrosscheckBadge value={l.crosscheck} /> },
    { key: "src", header: "출처", render: (l) => (l.source_url ? <a href={l.source_url} target="_blank" rel="noreferrer">🔗</a> : "확인 필요") },
  ];
  return <Table columns={columns} rows={rows} rowKey={(l) => l.id} />;
}
