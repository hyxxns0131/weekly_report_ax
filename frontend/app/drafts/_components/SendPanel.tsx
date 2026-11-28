"use client";
// B2-05·08 Gmail 초안함 · 승인 · 발송 (KHW). 발송은 승인된 초안만, [발송]은 확인 창을 한 번 더 띄운다.
// 초안을 바꿔 고르면 page.tsx가 key로 이 부품을 새로 만든다: 안내 문구·경고 확인 체크가 다른 초안으로 넘어가지 않게.
import { useState } from "react";
import { color } from "../../../components/ui/tokens";
import { approve, send, toGmailDraft } from "../../../lib/api/b2/send";
import type { SendInfo } from "../../../lib/types/b2";
import type { MailDraft } from "../../../lib/types/core";
import { isDropped } from "./DraftList";

const TEXT = {
  dropped:
    "이번 주 안내 대상에서 빠진 고객사 초안입니다. 승인·발송할 수 없습니다. 고객사 판단 화면에서 다시 [유지]하고 초안을 다시 만들면 풀립니다.",
  ack: "경고를 확인했습니다",
  gmail: "Gmail 초안함에 저장",
  gmailAgain: "Gmail 초안함에 다시 저장",
  gmailOk: "Gmail 초안함에 저장했습니다. Gmail [임시보관함]에서 볼 수 있습니다.",
  gmailSaved: "Gmail 초안함에 저장됨 (본문을 고쳤다면 다시 저장해 주세요. 발송할 때는 승인한 본문으로 자동으로 맞춥니다)",
  approve: "승인",
  approveOk: "승인했습니다.",
  send: "발송",
  sendOk: "발송했습니다.",
  confirmSend: "이 메일을 지금 보낼까요? 보낸 메일은 되돌릴 수 없습니다.",
  sendOff: "발송 꺼짐 (MAIL_SEND_ENABLED=false)",
  sent: "발송함",
  noStaffTo: "받는 사람 미설정 (.env GMAIL_STAFF_TO, KHS)",
  noCustomerTo: "고객사 메일 주소는 연결 전입니다(미팅 뒤). Gmail 초안함에 저장한 뒤 Gmail에서 받는 사람을 넣어 주세요.",
  staffTo: (n: number) => `받는 사람: 담당자 ${n}명`,
};

export function SendPanel({ draft, info, onChanged }: { draft: MailDraft; info: SendInfo; onChanged: () => void }) {
  const [ack, setAck] = useState(false);
  const [msg, setMsg] = useState<{ text: string; error: boolean } | null>(null);
  const [busy, setBusy] = useState(false);
  const run = async (fn: () => Promise<unknown>, ok: string) => {
    setBusy(true);
    setMsg(null);
    try {
      await fn();
      setMsg({ text: ok, error: false });
      onChanged();
    } catch (e) {
      setMsg({ text: e instanceof Error ? e.message : "실패", error: true });
    } finally {
      setBusy(false);
    }
  };
  const dropped = isDropped(draft);
  const sent = draft.status === "sent";
  const staff = draft.kind === "staff_summary";
  const hasTo = staff && info.staff_to_count > 0;
  // globals.css의 button.primary가 비활성 회색을 덮어써서, 막혔을 때는 primary를 빼서 회색으로 보이게 한다
  const approveBlocked = busy || dropped || draft.status !== "draft" || (draft.warnings.length > 0 && !ack);
  const sendBlocked = busy || draft.status !== "approved" || !info.mail_send_enabled || !hasTo;
  const onSend = () => {
    if (!window.confirm(TEXT.confirmSend)) return;
    void run(() => send(draft.id), TEXT.sendOk);
  };
  return (
    <div style={{ marginTop: 8 }}>
      {dropped && (
        <p role="alert" style={{ color: color.danger, fontWeight: 700 }}>{TEXT.dropped}</p>
      )}
      {!dropped && draft.warnings.length > 0 && draft.status === "draft" && (
        <label style={{ display: "block", color: color.warning }}>
          <input type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} /> {TEXT.ack}
        </label>
      )}
      <p style={{ color: color.muted, margin: "4px 0" }}>
        {staff ? (hasTo ? TEXT.staffTo(info.staff_to_count) : TEXT.noStaffTo) : TEXT.noCustomerTo}
      </p>
      <button type="button" disabled={busy || dropped || sent}
        onClick={() => run(() => toGmailDraft(draft.id), TEXT.gmailOk)}>
        {draft.gmail_draft_id ? TEXT.gmailAgain : TEXT.gmail}
      </button>{" "}
      <button type="button" className={approveBlocked ? undefined : "primary"} disabled={approveBlocked}
        onClick={() => run(() => approve(draft.id, ack), TEXT.approveOk)}>{TEXT.approve}</button>{" "}
      <button type="button" className={sendBlocked ? undefined : "primary"} disabled={sendBlocked} onClick={onSend}>
        {TEXT.send}
      </button>
      {!info.mail_send_enabled && <span style={{ color: color.muted }}> {TEXT.sendOff}</span>}
      {draft.gmail_draft_id && !sent && <p style={{ color: color.muted }}>{TEXT.gmailSaved}</p>}
      {draft.approved_by && <p style={{ color: color.muted }}>승인: {draft.approved_by} · {draft.approved_at}</p>}
      {sent && <p style={{ color: color.muted }}>{TEXT.sent}: {draft.sent_at}</p>}
      {msg && (
        <p role={msg.error ? "alert" : undefined} style={{ color: msg.error ? color.danger : color.muted }}>{msg.text}</p>
      )}
    </div>
  );
}
