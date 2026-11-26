"use client";
// B2-05·08 Gmail 초안함 · 승인 · 발송 (KHW). 발송은 승인된 초안만, 확인 대화상자 없이 버튼 비활성으로 막는다.
import { useState } from "react";
import { color } from "../../../components/ui/tokens";
import { approve, send, toGmailDraft } from "../../../lib/api/b2/send";
import type { MailDraft } from "../../../lib/types/core";
import { isDropped } from "./DraftList";

const DROPPED_NOTICE =
  "이번 주 안내 대상에서 빠진 고객사 초안입니다. 승인·발송할 수 없습니다. 고객사 판단 화면에서 다시 [유지]하고 초안을 다시 만들면 풀립니다.";

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
  const dropped = isDropped(draft);
  // globals.css의 button.primary가 비활성 회색을 덮어써서, 막혔을 때는 primary를 빼서 회색으로 보이게 한다
  const approveBlocked = dropped || draft.status !== "draft" || (draft.warnings.length > 0 && !ack);
  return (
    <div style={{ marginTop: 8 }}>
      {dropped && (
        <p role="alert" style={{ color: color.danger, fontWeight: 700 }}>{DROPPED_NOTICE}</p>
      )}
      {!dropped && draft.warnings.length > 0 && draft.status === "draft" && (
        <label style={{ display: "block", color: color.warning }}>
          <input type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} /> 경고를 확인했습니다
        </label>
      )}
      <button type="button" disabled={dropped} onClick={() => run(() => toGmailDraft(draft.id), "Gmail 초안함에 저장했습니다.")}>Gmail 초안함에 저장</button>{" "}
      <button type="button" className={approveBlocked ? undefined : "primary"} disabled={approveBlocked}
        onClick={() => run(() => approve(draft.id, ack), "승인했습니다.")}>승인</button>{" "}
      <button type="button" disabled={draft.status !== "approved" || !sendEnabled}
        onClick={() => run(() => send(draft.id), "발송했습니다.")}>발송</button>
      {!sendEnabled && <span style={{ color: color.muted }}> 발송 꺼짐 (MAIL_SEND_ENABLED=false)</span>}
      {draft.approved_by && <p style={{ color: color.muted }}>승인: {draft.approved_by} · {draft.approved_at}</p>}
      {msg && <p style={{ color: color.muted }}>{msg}</p>}
    </div>
  );
}
