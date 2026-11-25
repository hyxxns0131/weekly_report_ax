// B2-01 보고서 조립 API (KHW)
import { apiFetch } from "../client";
import type { ReportOut } from "../../types/b2";

export const buildReport = (runId: number) =>
  apiFetch<ReportOut>(`/b2/runs/${runId}/report`, { method: "POST" });

// 새 개정이 없는 주에 섹션 2에 넣을 재안내 글 (null이면 지움). 저장 후 보고서를 다시 조립해야 반영된다.
export const setReannounce = (runId: number, text: string | null) =>
  apiFetch<{ text: string | null }>(`/b2/runs/${runId}/report/reannounce`, {
    method: "PUT",
    body: JSON.stringify({ text }),
  });
