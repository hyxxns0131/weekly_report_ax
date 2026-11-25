"use client";
// 메뉴 7개와 로그인 확인 (KHS 고정 파일). 바꿀 일이 있으면 PR "변경 요청"에 적는다.
// 화면 쪽 확인: 토큰이 없거나 /api/core/auth/me가 실패하면 /login으로 보낸다.
// 실제 차단은 FastAPI(require_login)가 한다 (AGENTS.md 0-6-1).

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";
import { color } from "../components/ui/tokens";
import "./globals.css";
import { getToken } from "../lib/api/client";
import { getMe, logout } from "../lib/api/core";

const TEXT = {
  title: "수입식품 주간 검역 보고서",
  logout: "로그아웃",
  checking: "로그인 확인 중…",
};

const MENU: { href: string; label: string }[] = [
  { href: "/", label: "이번 주 현황" },
  { href: "/collect/", label: "수집·선별" },
  { href: "/customers/", label: "고객사 판단" },
  { href: "/law/", label: "법령 개정" },
  { href: "/drafts/", label: "보고서·메일" },
  { href: "/evaluate/", label: "검증" },
  { href: "/settings/", label: "설정" },
];

function normalize(path: string): string {
  return path.endsWith("/") ? path : `${path}/`;
}

export default function RootLayout({ children }: { children: ReactNode }) {
  const pathname = normalize(usePathname() ?? "/");
  const router = useRouter();
  const isLogin = pathname === "/login/";
  const [user, setUser] = useState<string | null>(null);

  useEffect(() => {
    if (isLogin) return;
    if (!getToken()) {
      router.replace("/login/");
      return;
    }
    getMe()
      .then((me) => setUser(me.username))
      .catch(() => router.replace("/login/"));
  }, [isLogin, pathname, router]);

  async function onLogout() {
    await logout().catch(() => undefined);
    setUser(null);
    router.replace("/login/");
  }

  return (
    <html lang="ko">
      <head>
        <title>{TEXT.title}</title>
      </head>
      <body>
        {isLogin ? (
          children
        ) : user === null ? (
          <p style={{ padding: 24, color: color.muted }}>{TEXT.checking}</p>
        ) : (
          <div style={{ display: "flex", minHeight: "100vh", background: `linear-gradient(to right, ${color.sidebar} 0 219px, ${color.border} 219px 220px, transparent 220px)` }}>
            <nav
              className="app-nav"
              style={{ width: 220, flexShrink: 0, padding: "20px 14px", background: color.sidebar, borderRight: `1px solid ${color.border}`, position: "sticky", top: 0, height: "100vh" }}
            >
              <div style={{ padding: "4px 14px 20px", fontSize: 17, fontWeight: 800, color: color.info, lineHeight: 1.4 }}>
                {TEXT.title}
              </div>
              {MENU.map((m) => (
                <Link key={m.href} href={m.href} className={pathname === m.href ? "active" : undefined}>
                  {m.label}
                </Link>
              ))}
            </nav>
            <main style={{ flex: 1, minWidth: 0 }}>
              <header
                style={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: 12, padding: "12px 32px", background: color.surface, borderBottom: `1px solid ${color.border}` }}
              >
                <span style={{ color: color.muted }}>👤 {user}</span>
                <button type="button" onClick={onLogout}>
                  {TEXT.logout}
                </button>
              </header>
              <div style={{ padding: "24px 32px", maxWidth: 1400 }}>{children}</div>
            </main>
          </div>
        )}
      </body>
    </html>
  );
}
