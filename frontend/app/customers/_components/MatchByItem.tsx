"use client";
// B1-11 항목별 고객사 판단 (LSH)
import { Badge } from "../../../components/ui/Badge";
import { type Column, Table } from "../../../components/ui/Table";
import type { MatchRow } from "../../../lib/types/b1";

export function isOn(m: MatchRow): boolean {
  return m.final_matched ?? m.ai_matched;
}

export function MatchByItem({ rows, onSet }: { rows: MatchRow[]; onSet: (m: MatchRow, v: boolean) => void }) {
  const columns: Column<MatchRow>[] = [
    { key: "item", header: "항목", render: (m) => (m.item_url ? <a href={m.item_url} target="_blank" rel="noreferrer">{m.item_title}</a> : m.item_title) },
    { key: "cust", header: "고객사", render: (m) => `${m.customer_name} (${m.customer_id})` },
    { key: "reason", header: "근거", render: (m) => m.reason },
    {
      key: "conf",
      header: "신뢰도",
      render: (m) => (m.confidence === "high" ? <Badge tone="success">높음</Badge> : <Badge tone="warning">중간 · 검토 필요</Badge>),
    },
    {
      key: "state",
      header: "상태",
      render: (m) =>
        m.final_matched === null ? (
          <Badge tone="info">AI 결과 · 담당자 확인 전</Badge>
        ) : (
          <Badge tone="warning">담당자 {m.final_matched ? "유지" : "제외"}</Badge>
        ),
    },
    {
      key: "act",
      header: "담당자",
      render: (m) => (
        <>
          <button type="button" disabled={isOn(m) && m.final_matched !== null} onClick={() => onSet(m, true)}>유지</button>{" "}
          <button type="button" disabled={!isOn(m)} onClick={() => onSet(m, false)}>제외</button>
        </>
      ),
    },
  ];
  return <Table columns={columns} rows={rows} rowKey={(m) => `${m.item_id}|${m.customer_id}`} />;
}
