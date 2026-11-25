// B1-08 선별 목록 (LSH)
import { CATEGORY_TEXT, LabelBadge } from "../../../components/ui/LabelBadge";
import { type Column, Table } from "../../../components/ui/Table";
import type { ItemRow } from "../../../lib/types/b1";

export function ClassifyTable({ rows, onSelect, selectedId }: {
  rows: ItemRow[];
  onSelect: (row: ItemRow) => void;
  selectedId: string | null;
}) {
  const columns: Column<ItemRow>[] = [
    { key: "cat", header: "구분", render: (r) => (r.selection ? CATEGORY_TEXT[r.selection.final_category ?? r.selection.ai_category] : "—") },
    { key: "date", header: "일자", render: (r) => r.raw.posted_at ?? "—" },
    {
      key: "title",
      header: "제목",
      render: (r) => (
        <button type="button" onClick={() => onSelect(r)} style={{ background: "none", border: "none", padding: 0, cursor: "pointer", textAlign: "left", fontWeight: r.raw.id === selectedId ? 700 : 400 }}>
          {r.raw.title}
        </button>
      ),
    },
    { key: "label", header: "판정", render: (r) => <LabelBadge selection={r.selection} /> },
    { key: "reason", header: "사유", render: (r) => r.selection?.ai_reason ?? "—" },
    { key: "url", header: "원문", render: (r) => (r.raw.url ? <a href={r.raw.url} target="_blank" rel="noreferrer">🔗</a> : "—") },
  ];
  return <Table columns={columns} rows={rows} rowKey={(r) => r.raw.id} />;
}
