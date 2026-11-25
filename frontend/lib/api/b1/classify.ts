// B1-08 선별 화면 API (LSH)
import { apiFetch } from "../client";
import type { AnalyzeResult } from "../../types/b1";
import type { Label, Selection } from "../../types/core";

export const analyze = (runId: number) =>
  apiFetch<AnalyzeResult>(`/b1/runs/${runId}/analyze`, { method: "POST" });

export const setLabel = (itemId: string, finalLabel: Label) =>
  apiFetch<Selection>(`/b1/items/${encodeURIComponent(itemId)}/selection`, {
    method: "PATCH",
    body: JSON.stringify({ final_label: finalLabel }),
  });
