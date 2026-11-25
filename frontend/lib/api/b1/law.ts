// B1-12~14 법령 개정 화면 API (LSH)
import { apiFetch } from "../client";
import type { LawFetchResult } from "../../types/b1";
import type { LawChange } from "../../types/core";

export const fetchLaw = (runId: number) =>
  apiFetch<LawFetchResult>(`/b1/runs/${runId}/law`, { method: "POST" });

export const getLaw = (runId: number) => apiFetch<LawChange[]>(`/b1/runs/${runId}/law`);

export const saveLaw = (lawId: string, patch: { final_summary?: string; related_food_types?: string[] }) =>
  apiFetch<LawChange>(`/b1/law/${encodeURIComponent(lawId)}`, { method: "PATCH", body: JSON.stringify(patch) });
