// B2-01 보고서 조립 API (KHW)
import { apiFetch } from "../client";
import type { ReportOut } from "../../types/b2";

export const buildReport = (runId: number) =>
  apiFetch<ReportOut>(`/b2/runs/${runId}/report`, { method: "POST" });
