"use client";
// 사이드바(역할 3개 + 설정)·맨 위 줄·알림 종·단계 바와 로그인 확인 (KHS 고정 파일, DESIGN.md 1-0·3-2).
// 바꿀 일이 있으면 PR "변경 요청"에 적는다.
// 화면 쪽 확인: 토큰이 없거나 /api/core/auth/me가 실패하면 /login으로 보낸다.
// 실제 차단은 FastAPI(require_login)가 한다 (AGENTS.md 0-6-1).

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { type ReactNode, Suspense, useEffect, useState } from "react";
import { NoticeBell } from "../components/ui/NoticeBell";
import { RunStatusProvider, useRunStatus } from "../components/ui/RunStatusContext";
import { StepBar } from "../components/ui/StepBar";
import { groupOfPath, stepOfLocation } from "../components/ui/steps";
import { color } from "../components/ui/tokens";
import "./globals.css";
import { getToken } from "../lib/api/client";
import { getMe, logout } from "../lib/api/core";
import type { Run, StepGroup } from "../lib/types/core";

const TEXT = {
  title: "수입식품 주간 검역 보고서",
  logout: "로그아웃",
  checking: "로그인 확인 중…",
  nowWeek: "지금",
  navOpen: "메뉴 열기",
  navClose: "메뉴 닫기",
  menu: "메뉴",
  noRun: "이번 주 실행 없음",
  ruleLast: "월~목에 실행 → 지난주 기준",
  ruleThis: "금~일에 실행 → 이번 주 기준",
};

const MENU: { href: string; label: string; owner: string; group: StepGroup | "home" }[] = [
  { href: "/", label: "이번 주 현황", owner: "KHS", group: "home" },
  { href: "/collect/", label: "자료 선별·고객사 매칭", owner: "LSH", group: "b1" },
  { href: "/drafts/", label: "보고서·메일", owner: "KHW", group: "b2" },
];

const BOTTOM: { href: string; label: string }[] = [
  { href: "/settings/", label: "설정" },
  { href: "/connections/", label: "연결 설정" },
];

const NAV_KEY = "weekly.nav";

const DAYS = ["일", "월", "화", "수", "목", "금", "토"];

function normalize(path: string): string {
  return path.endsWith("/") ? path : `${path}/`;
}

function day(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  const dow = DAYS[new Date(y, m - 1, d).getDay()];
  return `${m}/${d}(${dow})`;
}

function iso(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** 오늘이 속한 주(월~일)와 주차. 주차 규칙은 core/period.py week_of_month와 같다(일요일 시작, 1일이 든 주 = 1주차) */
function currentWeek(today: Date = new Date()): { label: string; start: string; end: string } {
  const monday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - ((today.getDay() + 6) % 7));
  const sunday = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + 6);
  const offset = new Date(monday.getFullYear(), monday.getMonth(), 1).getDay();
  const week = Math.floor((monday.getDate() + offset - 1) / 7) + 1;
  return {
    label: `${monday.getFullYear()}년 ${monday.getMonth() + 1}월 ${week}주차`,
    start: iso(monday),
    end: iso(sunday),
  };
}

function ruleText(run: Run): string {
  const [y, m, d] = run.reference_date.split("-").map(Number);
  const dow = new Date(y, m - 1, d).getDay();
  return dow === 0 || dow >= 5 ? TEXT.ruleThis : TEXT.ruleLast;
}

/** 사이드바 배지: 자료 선별·고객사 매칭 "검토 n", 보고서·메일 "승인 대기 n". 0이면 숨긴다 */
function useBadges(): Record<StepGroup, string | null> {
  const { state } = useRunStatus();
  if (state.kind !== "ok") return { b1: null, b2: null };
  const c = state.status.counts;
  return {
    b1: c.review_needed > 0 ? `검토 ${c.review_needed}` : null,
    b2: c.approval_waiting > 0 ? `승인 대기 ${c.approval_waiting}` : null,
  };
}

function Sidebar({ pathname, user, onLogout }: { pathname: string; user: string; onLogout: () => void }) {
  const badges = useBadges();
  const activeGroup = groupOfPath(pathname);
  return (
    <nav
      className="app-nav"
      style={{
        width: 236,
        flexShrink: 0,
        padding: "28px 16px 20px",
        background: color.sidebar,
        borderTopRightRadius: 48,
        alignSelf: "stretch",
        minHeight: "calc(100vh - 36px - 84px)",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div className="nav-label">{TEXT.menu}</div>
      {MENU.map((m) => {
        const active = m.group === "home" ? pathname === "/" : activeGroup === m.group;
        const badge = m.group === "home" ? null : badges[m.group];
        return (
          <Link key={m.href} href={m.href} className={active ? "active" : undefined} aria-current={active ? "page" : undefined}>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span>{m.label}</span>
              <span style={{ fontSize: 12, opacity: 0.7 }}>· {m.owner}</span>
              {badge && <span className="nav-badge">{badge}</span>}
            </span>
          </Link>
        );
      })}
      <div style={{ marginTop: "auto", borderTop: "1px solid rgba(255,255,255,0.25)", paddingTop: 12 }}>
        <div style={{ display: "flex", gap: 4 }}>
          {BOTTOM.map((b) => (
            <Link key={b.href} href={b.href} className={`small${pathname === b.href ? " active" : ""}`}>
              {b.label}
            </Link>
          ))}
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 6px 0" }}>
          <span style={{ color: "#fff", fontSize: 14, fontWeight: 600 }}>👤 {user}</span>
          <button type="button" onClick={onLogout} style={{ padding: "4px 12px", fontSize: 13, background: "#fff", border: "none" }}>
            {TEXT.logout}
          </button>
        </div>
      </div>
    </nav>
  );
}

function TopBar({ refreshKey, navOpen, onToggleNav }: { refreshKey: string; navOpen: boolean; onToggleNav: () => void }) {
  // 맨 위 줄은 화면 전체 너비: 왼쪽 프로그램 이름(사이드바 위), 가운데 보고 주차, 오른쪽 실행 기준·알림 종
  const { state } = useRunStatus();
  const run = state.kind === "ok" ? state.status.run : null;
  const now = currentWeek();
  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        height: 84,
        padding: "0 32px 0 28px",
        background: color.surface,
        position: "relative",
        zIndex: 40,
      }}
    >
      <button
        type="button"
        onClick={onToggleNav}
        aria-label={navOpen ? TEXT.navClose : TEXT.navOpen}
        aria-expanded={navOpen}
        title={navOpen ? TEXT.navClose : TEXT.navOpen}
        style={{ width: 40, height: 40, padding: 0, flexShrink: 0, fontSize: 20, lineHeight: 1, border: "none", background: color.card }}
      >
        <span aria-hidden>☰</span>
      </button>
      <div style={{ width: 196, flexShrink: 0, display: "flex", alignItems: "center", gap: 10, fontSize: 17, fontWeight: 800, color: color.primary, lineHeight: 1.3, wordBreak: "keep-all" }}>
        <span aria-hidden style={{ width: 30, height: 30, borderRadius: 9, background: color.primary, color: "#fff", display: "grid", placeItems: "center", fontSize: 15 }}>검</span>
        {TEXT.title}
      </div>
      <div style={{ fontWeight: 700, background: color.card, padding: "9px 18px", borderRadius: 999, marginLeft: 12 }}>
        {run ? (
          <>
            <span style={{ color: color.muted, fontWeight: 500 }}>보고 주차 </span>
            {run.week_label}
            <span style={{ color: color.muted, fontWeight: 500 }}>
              {" "}
              · {day(run.period_start)} ~ {day(run.period_end)}
            </span>
          </>
        ) : (
          <span style={{ color: color.muted }}>{state.kind === "loading" ? "" : TEXT.noRun}</span>
        )}
      </div>
      <div style={{ fontWeight: 700, padding: "9px 4px", whiteSpace: "nowrap" }}>
        <span style={{ color: color.muted, fontWeight: 500 }}>{TEXT.nowWeek} </span>
        {now.label}
        <span style={{ color: color.muted, fontWeight: 500 }}>
          {" "}
          · {day(now.start)} ~ {day(now.end)}
        </span>
      </div>
      <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 12 }}>
        {run && (
          <span style={{ fontSize: 13, color: color.info, background: color.primarySoft, padding: "4px 10px", borderRadius: 999 }}>
            {ruleText(run)}
          </span>
        )}
        <NoticeBell runId={run?.id ?? null} refreshKey={refreshKey} />
      </div>
    </header>
  );
}

/** 경로와 ?step=으로 지금 단계를 찾아 단계 바를 띄운다. useSearchParams라서 Suspense 안에 둔다 */
function PageStepBar({ pathname }: { pathname: string }) {
  const params = useSearchParams();
  const loc = stepOfLocation(pathname, params.get("step"));
  if (!loc) return null;
  return <StepBar group={loc.group} current={loc.key} />;
}

function SearchKey({ onChange }: { onChange: (s: string) => void }) {
  const params = useSearchParams();
  const s = params.toString();
  useEffect(() => onChange(s), [s, onChange]);
  return null;
}

export default function RootLayout({ children }: { children: ReactNode }) {
  const pathname = normalize(usePathname() ?? "/");
  const router = useRouter();
  const isLogin = pathname === "/login/";
  const [user, setUser] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  // 사이드바 열기·닫기. 마지막 상태를 브라우저에 기억한다 (서버 기능 없음)
  const [navOpen, setNavOpen] = useState(true);
  useEffect(() => {
    if (localStorage.getItem(NAV_KEY) === "closed") setNavOpen(false);
  }, []);
  function toggleNav() {
    setNavOpen((v) => {
      localStorage.setItem(NAV_KEY, v ? "closed" : "open");
      return !v;
    });
  }

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

  const refreshKey = `${pathname}?${search}`;

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
          <RunStatusProvider refreshKey={refreshKey}>
            <Suspense fallback={null}>
              <SearchKey onChange={setSearch} />
            </Suspense>
            <div className="app-frame" style={{ flexDirection: "column" }}>
              <TopBar refreshKey={refreshKey} navOpen={navOpen} onToggleNav={toggleNav} />
              <div style={{ display: "flex", flex: 1 }}>
                {navOpen && <Sidebar pathname={pathname} user={user} onLogout={onLogout} />}
                <main style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ padding: "8px 36px 32px", maxWidth: 1400 }}>
                    <Suspense fallback={null}>
                      <PageStepBar pathname={pathname} />
                    </Suspense>
                    {children}
                  </div>
                </main>
              </div>
            </div>
          </RunStatusProvider>
        )}
      </body>
    </html>
  );
}
