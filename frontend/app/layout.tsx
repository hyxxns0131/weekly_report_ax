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
    <nav className="app-nav" style={{ background: color.sidebar }}>
      <div className="nav-title">{TEXT.title}</div>
      <div className="nav-label">{TEXT.menu}</div>
      {MENU.map((m) => {
        const active = m.group === "home" ? pathname === "/" : activeGroup === m.group;
        const badge = m.group === "home" ? null : badges[m.group];
        return (
          <Link key={m.href} href={m.href} className={active ? "active" : undefined} aria-current={active ? "page" : undefined}>
            <span style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: "2px 6px" }}>
              <span style={{ whiteSpace: "nowrap" }}>{m.label}</span>
              <span className="nav-owner">· {m.owner}</span>
              {badge && <span className="nav-badge">{badge}</span>}
            </span>
          </Link>
        );
      })}
      <div className="nav-bottom">
        <div style={{ display: "flex", gap: 4 }}>
          {BOTTOM.map((b) => (
            <Link key={b.href} href={b.href} className={`small${pathname === b.href ? " active" : ""}`}>
              {b.label}
            </Link>
          ))}
        </div>
        <div className="nav-user">
          <span>👤 {user}</span>
          <button type="button" onClick={onLogout}>
            {TEXT.logout}
          </button>
        </div>
      </div>
    </nav>
  );
}

/** 맨 왼쪽 파란 둥근 띠: 프로그램 표시, 메뉴 열기·닫기(☰), 로그인한 사용자 첫 글자 */
function Rail({ user, navOpen, onToggleNav }: { user: string; navOpen: boolean; onToggleNav: () => void }) {
  return (
    <div className="app-rail">
      <span className="rail-logo" aria-hidden title={TEXT.title}>
        검
      </span>
      <button
        type="button"
        onClick={onToggleNav}
        aria-label={navOpen ? TEXT.navClose : TEXT.navOpen}
        aria-expanded={navOpen}
        title={navOpen ? TEXT.navClose : TEXT.navOpen}
      >
        <span aria-hidden>☰</span>
      </button>
      <span className="rail-user" aria-hidden title={user}>
        {user.slice(0, 1)}
      </span>
    </div>
  );
}

function TopBar({ refreshKey, navOpen }: { refreshKey: string; navOpen: boolean }) {
  // 맨 위 줄: 보고 주차(흰 둥근 칸), 지금 주차, 오른쪽 실행 기준·알림 종. 메뉴를 닫으면 프로그램 이름도 보인다
  const { state } = useRunStatus();
  const run = state.kind === "ok" ? state.status.run : null;
  const now = currentWeek();
  return (
    <header className="app-top">
      {!navOpen && <div style={{ fontSize: 17, fontWeight: 800, marginRight: 8, whiteSpace: "nowrap" }}>{TEXT.title}</div>}
      <div className="top-pill">
        {run ? (
          <>
            <span className="top-muted">보고 주차 </span>
            {run.week_label}
            <span className="top-muted">
              {" "}
              · {day(run.period_start)} ~ {day(run.period_end)}
            </span>
          </>
        ) : (
          <span className="top-muted">{state.kind === "loading" ? "" : TEXT.noRun}</span>
        )}
      </div>
      <div className="top-now">
        <span className="top-muted">{TEXT.nowWeek} </span>
        {now.label}
        <span className="top-muted">
          {" "}
          · {day(now.start)} ~ {day(now.end)}
        </span>
      </div>
      <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 12 }}>
        {run && <span className="top-rule">{ruleText(run)}</span>}
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
            <div className="app-frame">
              <Rail user={user} navOpen={navOpen} onToggleNav={toggleNav} />
              {navOpen && <Sidebar pathname={pathname} user={user} onLogout={onLogout} />}
              <div className={`app-main${pathname === "/" ? " home" : ""}`}>
                <TopBar refreshKey={refreshKey} navOpen={navOpen} />
                <main className="app-body" style={{ minWidth: 0 }}>
                  <div style={{ padding: "12px 36px 36px 30px", maxWidth: 1400 }}>
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
