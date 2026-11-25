// API 호출 공통 (KHS). 화면은 fetch를 직접 쓰지 않고 lib/api/<b1|b2>/<기능>.ts 함수만 쓴다.
// 로그인 토큰은 여기서 모든 요청에 자동으로 붙인다(C-08). 각 담당자는 따로 처리하지 않는다.

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000/api";
const TOKEN_KEY = "weekly_report_token";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export function getToken(): string | null {
  return typeof window === "undefined" ? null : window.sessionStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.sessionStorage.removeItem(TOKEN_KEY);
}

function detailOf(body: unknown, fallback: string): string {
  if (typeof body === "object" && body !== null && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "서버에 연결할 수 없습니다. 백엔드(uvicorn)가 켜져 있는지 확인해 주세요.");
  }

  if (res.status === 401 && !path.startsWith("/core/auth/login")) {
    clearToken();
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login/";
    }
  }
  if (!res.ok) {
    const body: unknown = await res.json().catch(() => null);
    throw new ApiError(res.status, detailOf(body, `요청 실패 (${res.status})`));
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
