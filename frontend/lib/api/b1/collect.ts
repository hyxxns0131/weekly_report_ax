// B1-01~07 수집 화면 API (LSH)
import { apiFetch } from "../client";
import type { CollectResult, ItemRow, SourceStatus, UploadRequest } from "../../types/b1";

export const upload = (runId: number, body: UploadRequest) =>
  apiFetch<CollectResult>(`/b1/runs/${runId}/upload`, { method: "POST", body: JSON.stringify(body) });

export const collect = (runId: number, sources?: string[]) =>
  apiFetch<CollectResult[]>(`/b1/runs/${runId}/collect`, {
    method: "POST",
    body: JSON.stringify({ sources: sources ?? null }),
  });

export const getSourceStatus = (runId: number) => apiFetch<SourceStatus[]>(`/b1/runs/${runId}/sources`);

export const getItems = (runId: number, label?: string) =>
  apiFetch<ItemRow[]>(`/b1/runs/${runId}/items${label && label !== "all" ? `?label=${label}` : ""}`);
