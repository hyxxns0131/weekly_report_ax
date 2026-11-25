// B1-11 고객사 판단 화면 API (LSH)
import { apiFetch } from "../client";
import type { MatchRow } from "../../types/b1";
import type { CustomerMatch } from "../../types/core";

export const getMatches = (runId: number) => apiFetch<MatchRow[]>(`/b1/runs/${runId}/matches`);

export const setMatch = (itemId: string, customerId: string, finalMatched: boolean) =>
  apiFetch<CustomerMatch>(`/b1/matches/${encodeURIComponent(itemId)}/${encodeURIComponent(customerId)}`, {
    method: "PATCH",
    body: JSON.stringify({ final_matched: finalMatched }),
  });
