// 공통 API (KHS): 상태 확인, 로그인(C-08), 주간 실행·현황(C-06)
import { apiFetch, clearToken, setToken } from "./client";
import type { AiProvider, AiStatus, AiTest, ConnId, ConnStatus, Health, LoginResponse, Me, NoticeAction, NoticeList, Run, RunStatus } from "../types/core";

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

// 알림 (C-06, DESIGN.md 3-2). 읽음·지움 기록자는 서버가 로그인 사용자로 채운다.
export const getNotices = (runId: number) => apiFetch<NoticeList>(`/core/runs/${runId}/notices`);
export const markNotice = (noticeId: string, action: NoticeAction, runId: number) =>
  apiFetch<unknown>(`/core/notices/${encodeURIComponent(noticeId)}`, {
    method: "PATCH",
    body: JSON.stringify({ action, run_id: runId }),
  });

// AI 연결 상태·연결 검사·모델 선택 (C-02)
export const getAiStatus = () => apiFetch<AiStatus>("/core/ai/status");

export const setAiChoice = (provider: AiProvider, model: string) =>
  apiFetch<AiStatus>("/core/ai/settings", {
    method: "PUT",
    body: JSON.stringify({ provider, model }),
  });

export const testAi = () => apiFetch<AiTest>("/core/ai/test", { method: "POST" });

// 연결 설정 (C-01)
export const getConnections = () => apiFetch<ConnStatus[]>("/core/connections");
export const testConnection = (id: ConnId) =>
  apiFetch<ConnStatus>(`/core/connections/${id}/test`, { method: "POST" });
