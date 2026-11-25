"use client";
// B2-05·08 Gmail 초안함 · 승인 · 발송 (KHW). 발송은 승인된 초안만, 확인 대화상자 없이 버튼 비활성으로 막는다.
import { useState } from "react";
import { color } from "../../../components/ui/tokens";
import { approve, send, toGmailDraft } from "../../../lib/api/b2/send";
import type { MailDraft } from "../../../lib/types/core";

export function SendPanel({ draft, sendEnabled, onChanged }: { draft: MailDraft; sendEnabled: boolean; onChanged: () => void }) {
  const [ack, setAck] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const run = async (fn: () => Promise<unknown>, ok: string) => {
    try {
      await fn();
      setMsg(ok);
      onChanged();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "실패");
    }
  };
  return (
    <div style={{ marginTop: 8 }}>
      {draft.warnings.length > 0 && draft.status === "draft" && (
        <label style={{ display: "block", color: color.warning }}>
          <input type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} /> 경고를 확인했습니다
        </label>
      )}
      <button type="button" onClick={() => run(() => toGmailDraft(draft.id), "Gmail 초안함에 저장했습니다.")}>Gmail 초안함에 저장</button>{" "}
      <button type="button" className="primary" disabled={draft.status !== "draft" || (draft.warnings.length > 0 && !ack)}
        onClick={() => run(() => approve(draft.id, ack), "승인했습니다.")}>승인</button>{" "}
      <button type="button" disabled={draft.status !== "approved" || !sendEnabled}
        onClick={() => run(() => send(draft.id), "발송했습니다.")}>발송</button>
      {!sendEnabled && <span style={{ color: color.muted }}> 발송 꺼짐 (MAIL_SEND_ENABLED=false)</span>}
      {draft.approved_by && <p style={{ color: color.muted }}>승인: {draft.approved_by} · {draft.approved_at}</p>}
      {msg && <p style={{ color: color.muted }}>{msg}</p>}
    </div>
  );
}
