// B2-02~04 메일 초안 API (KHW)
import { apiFetch } from "../client";
import type { DraftHistoryRow } from "../../types/b2";
import type { MailDraft } from "../../types/core";

export const makeDrafts = (runId: number) =>
  apiFetch<MailDraft[]>(`/b2/runs/${runId}/drafts`, { method: "POST" });

export const getDrafts = (runId: number) => apiFetch<MailDraft[]>(`/b2/runs/${runId}/drafts`);

export const saveDraft = (draftId: number, finalBody: string) =>
  apiFetch<MailDraft>(`/b2/drafts/${draftId}`, { method: "PATCH", body: JSON.stringify({ final_body: finalBody }) });

export const getHistory = (draftId: number) => apiFetch<DraftHistoryRow[]>(`/b2/drafts/${draftId}/history`);
