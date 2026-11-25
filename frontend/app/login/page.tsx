"use client";
// 로그인 (C-08, KHS). 첫 화면. DESIGN.md 1-2.

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { color } from "../../components/ui/tokens";
import { ApiError } from "../../lib/api/client";
import { login } from "../../lib/api/core";

const TEXT = {
  title: "수입식품 주간 검역 보고서",
  username: "아이디",
  password: "비밀번호",
  submit: "로그인",
  submitting: "확인 중…",
  failed: "아이디 또는 비밀번호가 맞지 않습니다",
};

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username, password);
      router.replace("/");
    } catch (err) {
      setError(err instanceof ApiError && err.status !== 401 ? err.message : TEXT.failed);
    } finally {
      setBusy(false);
    }
  }

  const field = { display: "block", width: "100%", padding: 8, marginTop: 4, boxSizing: "border-box" as const };

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh", background: color.frame }}>
      <form
        onSubmit={onSubmit}
        style={{ width: 360, padding: 36, background: color.surface, borderRadius: 28, boxShadow: "0 12px 40px rgba(10, 40, 100, 0.25)" }}
      >
        <h1 style={{ fontSize: 22, marginTop: 0, color: color.primary }}>{TEXT.title}</h1>
        <label style={{ display: "block", marginBottom: 12 }}>
          {TEXT.username}
          <input style={field} value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
        </label>
        <label style={{ display: "block", marginBottom: 16 }}>
          {TEXT.password}
          <input
            style={field}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        <button type="submit" disabled={busy} style={{ width: "100%", padding: 10 }}>
          {busy ? TEXT.submitting : TEXT.submit}
        </button>
        {error && (
          <p role="alert" style={{ color: color.danger, marginBottom: 0 }}>
            ⚠ {error}
          </p>
        )}
      </form>
    </div>
  );
}
