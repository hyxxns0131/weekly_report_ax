"use client";
// B2-04 수정 이력 (KHW)
import { useEffect, useState } from "react";
import { color } from "../../../components/ui/tokens";
import { getHistory } from "../../../lib/api/b2/drafts";
import type { DraftHistoryRow } from "../../../lib/types/b2";

export function HistoryPanel({ draftId, version }: { draftId: number; version: string }) {
  const [rows, setRows] = useState<DraftHistoryRow[]>([]);
  useEffect(() => {
    getHistory(draftId).then(setRows).catch(() => setRows([]));
  }, [draftId, version]);
  if (rows.length === 0) return null;
  return (
    <details style={{ marginTop: 8 }}>
      <summary>수정 이력 {rows.length}건</summary>
      <ul style={{ color: color.muted, fontSize: 13 }}>
        {rows.map((r) => <li key={r.edited_at + r.body.length}>{r.edited_at} · {r.edited_by}</li>)}
      </ul>
    </details>
  );
}
