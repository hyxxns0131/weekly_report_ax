// B2-06 검증 API (KHW)
import { apiFetch } from "../client";
import type { EvalResult } from "../../types/core";

export const getGoldenWeeks = () => apiFetch<string[]>("/b2/eval/weeks");

export const runEval = (runId: number, goldenWeek: string) =>
  apiFetch<EvalResult>("/b2/eval", { method: "POST", body: JSON.stringify({ run_id: runId, golden_week: goldenWeek }) });

export const getEval = (runId: number) => apiFetch<EvalResult | null>(`/b2/runs/${runId}/eval`);
