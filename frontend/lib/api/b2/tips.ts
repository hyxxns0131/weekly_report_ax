// B2-07 오늘의 팁 API (KHW)
import { apiFetch } from "../client";
import type { TipTopic } from "../../types/b2";

export const getTopics = () => apiFetch<TipTopic[]>("/b2/tips/topics");

export const setTip = (runId: number, tip: string | null) =>
  apiFetch<{ tip: string | null }>(`/b2/runs/${runId}/tip`, { method: "PUT", body: JSON.stringify({ tip }) });
