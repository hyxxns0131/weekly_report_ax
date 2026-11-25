// B2-06 지표 표 (KHW)
import { type Column, Table } from "../../../components/ui/Table";
import type { EvalResult } from "../../../lib/types/core";

type Row = { name: string; value: string };
const fmt = (v: number | null) => (v === null ? "—" : v.toFixed(2));

export function MetricTable({ result }: { result: EvalResult }) {
  const rows: Row[] = [
    { name: "선별 재현율(누락)", value: fmt(result.selection_recall) },
    { name: "선별 정밀도(과다)", value: fmt(result.selection_precision) },
    { name: "고객사 판단 재현율", value: fmt(result.match_recall) },
    { name: "고객사 판단 정밀도", value: fmt(result.match_precision) },
    { name: "검토 필요 비율", value: fmt(result.review_needed_ratio) },
    { name: "처리 시간", value: result.elapsed_sec === null ? "—" : `${result.elapsed_sec}초` },
  ];
  const columns: Column<Row>[] = [
    { key: "n", header: "지표", render: (r) => r.name },
    { key: "v", header: "이번", render: (r) => r.value },
    { key: "t", header: "목표", render: () => "확인 필요" },
  ];
  return <Table columns={columns} rows={rows} rowKey={(r) => r.name} />;
}
