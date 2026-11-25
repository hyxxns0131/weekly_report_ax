// B2-05·08 승인·발송 API (KHW). 자동 발송 없음: 승인 → 발송 버튼.
import { apiFetch } from "../client";
import type { SendInfo } from "../../types/b2";
import type { MailDraft } from "../../types/core";

export const getSendInfo = () => apiFetch<SendInfo>("/b2/send/info");

export const toGmailDraft = (draftId: number) =>
  apiFetch<MailDraft>(`/b2/drafts/${draftId}/gmail-draft`, { method: "POST" });

export const approve = (draftId: number, acknowledgeWarnings: boolean) =>
  apiFetch<MailDraft>(`/b2/drafts/${draftId}/approve`, {
    method: "POST",
    body: JSON.stringify({ acknowledge_warnings: acknowledgeWarnings }),
  });

export const send = (draftId: number) => apiFetch<MailDraft>(`/b2/drafts/${draftId}/send`, { method: "POST" });
