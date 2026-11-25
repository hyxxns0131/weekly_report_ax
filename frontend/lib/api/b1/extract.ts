// B1-09 추출 화면 API (LSH)
import { apiFetch } from "../client";
import type { ExtractedPatch } from "../../types/b1";
import type { ExtractedInfo } from "../../types/core";

export const saveExtracted = (itemId: string, patch: ExtractedPatch) =>
  apiFetch<ExtractedInfo>(`/b1/items/${encodeURIComponent(itemId)}/extracted`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
