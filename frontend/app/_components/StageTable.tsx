// 단계별 진행 표 (C-06, KHS)
import { StatusBadge } from "../../components/ui/StatusBadge";
import { type Column, Table } from "../../components/ui/Table";
import type { StageStatus } from "../../lib/types/core";

const COLUMNS: Column<StageStatus>[] = [
  { key: "name", header: "단계", render: (s) => s.name },
  { key: "status", header: "상태", render: (s) => <StatusBadge state={s.status} /> },
  { key: "count", header: "건수", render: (s) => (s.count ? `${s.count}건` : "—") },
];

export function StageTable({ stages }: { stages: StageStatus[] }) {
  return <Table columns={COLUMNS} rows={stages} rowKey={(s) => s.key} />;
}
