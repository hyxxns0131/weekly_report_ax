"use client";
// B1-15 고객사 키워드 보기 (LSH). 읽기 전용, 원본은 구글 드라이브.
import { useEffect, useState } from "react";
import { EmptyState } from "../../../components/ui/EmptyState";
import { ErrorState } from "../../../components/ui/ErrorState";
import { Loading } from "../../../components/ui/Loading";
import { type Column, Table } from "../../../components/ui/Table";
import { color } from "../../../components/ui/tokens";
import { getCustomers } from "../../../lib/api/b1/settings";
import type { CustomerSetting } from "../../../lib/types/b1";

type Kw = CustomerSetting["keywords"][number];

export function CustomerKeywords() {
  const [rows, setRows] = useState<CustomerSetting[] | null>(null);
  const [pick, setPick] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCustomers()
      .then((r) => { setRows(r); setPick(r[0]?.customer_id ?? ""); })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "오류"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!rows) return <Loading />;
  if (rows.length === 0) return <EmptyState message="고객사 설정이 없습니다. backend/config/b1/customers/ 에 고객사 파일을 넣어 주세요(실제 파일은 커밋 금지)." />;
  const c = rows.find((r) => r.customer_id === pick) ?? rows[0];
  const columns: Column<Kw>[] = [
    { key: "o", header: "원산지", render: (k) => k.origin_country ?? "전 국가" },
    { key: "f", header: "식품유형", render: (k) => k.food_type },
  ];
  return (
    <>
      고객사:{" "}
      <select value={c.customer_id} onChange={(e) => setPick(e.target.value)}>
        {rows.map((r) => <option key={r.customer_id} value={r.customer_id}>{r.customer_id} ({r.display_name})</option>)}
      </select>
      <div style={{ marginTop: 8 }}><Table columns={columns} rows={c.keywords} rowKey={(k) => `${k.origin_country}-${k.food_type}`} /></div>
      <p>제조사: {c.makers.join(", ") || "—"} · HS 코드: {c.hs_codes.join(", ") || "—"}</p>
      <p style={{ color: color.muted }}>읽기 전용 (원본은 구글 드라이브)</p>
    </>
  );
}
