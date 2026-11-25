"use client";
// B1-15 출처 설정 (LSH). 저장하면 config/b1/sources.json
import { useEffect, useState } from "react";
import { ErrorState } from "../../../components/ui/ErrorState";
import { Loading } from "../../../components/ui/Loading";
import { type Column, Table } from "../../../components/ui/Table";
import { color } from "../../../components/ui/tokens";
import { getSources, saveSources } from "../../../lib/api/b1/settings";
import type { SourceSetting } from "../../../lib/types/b1";

export function SourceSettings() {
  const [rows, setRows] = useState<SourceSetting[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    getSources().then(setRows).catch((e: unknown) => setError(e instanceof Error ? e.message : "오류"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!rows) return <Loading />;

  const update = (id: string, patch: Partial<SourceSetting>) =>
    setRows(rows.map((r) => (r.id === id ? { ...r, ...patch } : r)));

  const columns: Column<SourceSetting>[] = [
    { key: "name", header: "출처", render: (r) => r.name },
    { key: "on", header: "사용", render: (r) => <input type="checkbox" checked={r.enabled} onChange={(e) => update(r.id, { enabled: e.target.checked })} /> },
    {
      key: "mode",
      header: "방식",
      render: (r) => (
        <select value={r.mode} onChange={(e) => update(r.id, { mode: e.target.value })}>
          <option value="auto">자동</option>
          <option value="manual">수동</option>
        </select>
      ),
    },
    { key: "sec", header: "섹션", render: (r) => <input type="number" min={1} max={3} value={r.section} onChange={(e) => update(r.id, { section: Number(e.target.value) })} style={{ width: 48 }} /> },
    { key: "allowed", header: "약관 확인", render: (r) => <input value={r.allowed} onChange={(e) => update(r.id, { allowed: e.target.value })} style={{ width: 90 }} /> },
  ];

  return (
    <>
      <Table columns={columns} rows={rows} rowKey={(r) => r.id} />
      <button type="button" style={{ marginTop: 8 }} onClick={async () => { await saveSources(rows); setMsg("저장했습니다."); }}>저장</button>
      {msg && <span style={{ color: color.muted, marginLeft: 8 }}>{msg}</span>}
    </>
  );
}
