"use client";
// B2-04 수정 이력 (KHW). 그때 본문 펼쳐 보기 + [이 글로 되돌리기] (되돌려도 이력이 하나 더 쌓인다).
import { useEffect, useState } from "react";
import { color } from "../../../components/ui/tokens";
import { getHistory, saveDraft } from "../../../lib/api/b2/drafts";
import type { DraftHistoryRow } from "../../../lib/types/b2";
import type { MailDraft } from "../../../lib/types/core";

const TEXT = {
  title: "수정 이력",
  restore: "이 글로 되돌리기",
  current: "지금 본문",
  confirm: "이 본문으로 되돌릴까요? 승인된 초안이면 승인이 풀립니다.",
  restored: "되돌렸습니다.",
  failed: "되돌리지 못했습니다",
  loadFailed: "수정 이력을 불러오지 못했습니다",
};

export function HistoryPanel({ draft, onRestored }: { draft: MailDraft; onRestored: () => void }) {
  const [rows, setRows] = useState<DraftHistoryRow[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  const version = draft.final_body ?? "";
  useEffect(() => {
    getHistory(draft.id)
      .then((r) => { setRows(r); setMsg(null); })
      .catch(() => { setRows([]); setMsg(TEXT.loadFailed); });
  }, [draft.id, version]);

  if (rows.length === 0) return msg ? <p style={{ color: color.muted }}>{msg}</p> : null;
  const locked = draft.status === "sent";

  async function restore(body: string) {
    if (!window.confirm(TEXT.confirm)) return;
    try {
      await saveDraft(draft.id, body);
      setMsg(TEXT.restored);
      onRestored();
    } catch (e) {
      setMsg(`${TEXT.failed}: ${e instanceof Error ? e.message : ""}`);
    }
  }

  return (
    <details style={{ marginTop: 8 }}>
      <summary>{TEXT.title} {rows.length}건</summary>
      {msg && <p style={{ color: color.muted }}>{msg}</p>}
      <ul style={{ fontSize: 13, paddingLeft: 16 }}>
        {rows.map((r, i) => {
          const isCurrent = i === 0 && r.body === draft.final_body;
          return (
            <li key={`${r.edited_at}-${i}`} style={{ marginBottom: 6 }}>
              <details>
                <summary style={{ color: color.muted }}>
                  {r.edited_at} · {r.edited_by}{isCurrent ? ` (${TEXT.current})` : ""}
                </summary>
                <pre style={{ whiteSpace: "pre-wrap", background: color.background, padding: 8, margin: "4px 0" }}>{r.body}</pre>
                {!isCurrent && (
                  <button type="button" disabled={locked} onClick={() => void restore(r.body)}>{TEXT.restore}</button>
                )}
              </details>
            </li>
          );
        })}
      </ul>
    </details>
  );
}
