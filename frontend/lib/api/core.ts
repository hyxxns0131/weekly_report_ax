// 공통 API (KHS): 상태 확인, 로그인(C-08), 주간 실행·현황(C-06)
import { apiFetch, clearToken, setToken } from "./client";
import type { Health, LoginResponse, Me, Run, RunStatus } from "../types/core";

export const getHealth = () => apiFetch<Health>("/core/health");

export async function login(username: string, password: string): Promise<LoginResponse> {
  const res = await apiFetch<LoginResponse>("/core/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  setToken(res.token);
  return res;
}

export async function logout(): Promise<void> {
  try {
    await apiFetch<void>("/core/auth/logout", { method: "POST" });
  } finally {
    clearToken();
  }
}

export const getMe = () => apiFetch<Me>("/core/auth/me");

export const createRun = (referenceDate?: string) =>
  apiFetch<Run>("/core/runs", {
    method: "POST",
    body: JSON.stringify({ reference_date: referenceDate ?? null }),
  });

export const getLatestRun = () => apiFetch<Run | null>("/core/runs/latest");

export const getRunStatus = (runId: number) => apiFetch<RunStatus>(`/core/runs/${runId}/status`);
