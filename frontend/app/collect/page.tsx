"use client";
// 수집·선별 (B1-01~11, LSH). 데모 보드:
// 맨 위 넓은 상자 [고객사 선별하기] = 출처 수집 → 수입식품 선별 → 고객사 찾기를 한 번에.
// 그 아래 고객사마다 카드 하나 = 그 고객사 관련 항목 + [메일 초안 만들기](KHW B2-03 API 호출).
// DESIGN.md 4장 화면(업로드·출처 상태·분류 표·추출 패널)은 아래 "담당자용 자세히 보기" 접기 안에 그대로 둔다.

import { useCallback, useEffect, useState } from "react";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorState } from "../../components/ui/ErrorState";
import { Loading } from "../../components/ui/Loading";
import { AiStatusBar } from "../../components/ui/AiStatusBar";
import { color, space } from "../../components/ui/tokens";
import { analyze } from "../../lib/api/b1/classify";
import { collect, getItems, getSourceStatus } from "../../lib/api/b1/collect";
import { fetchLaw, getLaw } from "../../lib/api/b1/law";
import { getMatches } from "../../lib/api/b1/match";
import { getCustomers, getSources } from "../../lib/api/b1/settings";
import { getDrafts, makeDrafts } from "../../lib/api/b2/drafts";
import { createRun, getLatestRun } from "../../lib/api/core";
import type { CustomerSetting, ItemRow, OneClickData, SourceStatus as SourceRow } from "../../lib/types/b1";
import type { MailDraft, Run } from "../../lib/types/core";
import { BoardCard, CARD_HEIGHT, CARD_WIDTH, InnerBox } from "./_components/BoardCard";
import { ClassifyTable } from "./_components/ClassifyTable";
import { CustomerCard, type DraftState } from "./_components/CustomerCard";
import { ExtractPanel } from "./_components/ExtractPanel";
import { HelpTip } from "./_components/HelpTip";
import { buildLines, OneClickResult } from "./_components/OneClickResult";
import { SourceStatus } from "./_components/SourceStatus";
import { UploadPanel } from "./_components/UploadPanel";

const TEXT = {
  title: "수집·선별",
  aiUsage: "선별(관련·무관·검토 필요)과 본문형 자료 정보 추출에 씁니다",
  selectTag: "1단계 · 선별",
  selectTitle: "고객사 선별하기",
  selectDesc: "출처에서 이번 주 소식을 모으고, 수입식품 관련만 고른 뒤, 규칙대로 관련 고객사를 찾습니다.",
  selectHelp: [
    "① 출처 수집: 정보마루·식약처·경인청·법제처 (지금은 저장해 둔 데모 응답)",
    "② 선별: 순서형 규칙 Q1~Q4로 관련·무관·검토 필요",
    "③ 고객사 찾기: 같은 제조사 → HS 코드 → 원산지+식품유형 → 식품유형만",
  ],
  steps: ["① 출처 수집", "② 수입식품 선별", "③ 고객사 찾기"],
  runAll: "이번 주 자동 수집·분석",
  rerun: "다시 수집·분석",
  aiNote: "AI 결과 · 담당자 확인 전",
  notRun: "아직 실행 전",
  failedSources: "수집 실패 출처",
  noCustomers: "설정된 고객사가 없습니다. 설정 화면에서 고객사 키워드를 확인해 주세요.",
  noDraftForCustomer: "메일에 넣을 부적합·검사지시 항목이 없어 초안을 만들지 않았습니다.",
  allResults: "전체 결과 목록 보기 (관련 고객사 없는 항목·무관 항목 포함)",
  details: "담당자용 자세히 보기",
  lawSource: "법제처",
  unknownError: "처리 중 오류가 났습니다",
  collect: "자동 수집 (Supabase DB 포함)",
  analyze: "분석 실행",
  empty: "이번 주 자료가 없습니다. 위에서 자료를 올리거나 [자동 수집]을 눌러 주세요.",
  filters: [
    ["all", "전체"],
    ["relevant", "관련"],
    ["review_needed", "검토 필요"],
    ["irrelevant", "무관"],
  ] as const,
};

function CollectBody({ run }: { run: Run }) {
  const [rows, setRows] = useState<ItemRow[] | null>(null);
  const [sources, setSources] = useState<SourceRow[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [selected, setSelected] = useState<ItemRow | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [items, src] = await Promise.all([getItems(run.id, filter), getSourceStatus(run.id)]);
      setRows(items);
      setSources(src);
      setSelected((s) => (s ? items.find((i) => i.raw.id === s.raw.id) ?? null : null));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "불러오지 못했습니다");
    }
  }, [run.id, filter]);

  useEffect(() => {
    void load();
  }, [load]);

  async function act(fn: () => Promise<string>) {
    setBusy(true);
    try {
      setMsg(await fn());
      await load();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "실패");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <UploadPanel runId={run.id} onDone={(m) => { setMsg(m); void load(); }} />
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <button type="button" disabled={busy} onClick={() => act(async () => {
          const r = await collect(run.id);
          return r.map((x) => `${x.source}: ${x.message || x.status}`).join(" · ");
        })}>
          {TEXT.collect}
        </button>
        <button type="button" className="primary" disabled={busy} onClick={() => act(async () => {
          const r = await analyze(run.id);
          return `분석 완료: 전체 ${r.total} · 관련 ${r.relevant} · 검토 필요 ${r.review_needed} · 무관 ${r.irrelevant} · 고객사 판단 ${r.matches}건`;
        })}>
          {TEXT.analyze}
        </button>
        <span style={{ marginLeft: "auto" }}>
          필터:{" "}
          {TEXT.filters.map(([v, l]) => (
            <button key={v} type="button" onClick={() => setFilter(v)} className={filter === v ? "primary" : undefined}>
              {l}
            </button>
          ))}
        </span>
      </div>
      {msg && <p style={{ color: color.muted }}>{msg}</p>}
      <SourceStatus rows={sources} />
      {error && <ErrorState message={error} onRetry={load} />}
      {!error && rows === null && <Loading />}
      {!error && rows !== null && rows.length === 0 && <EmptyState message={TEXT.empty} />}
      {!error && rows !== null && rows.length > 0 && (
        <div style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
          <div style={{ flex: 1 }}>
            <ClassifyTable rows={rows} onSelect={setSelected} selectedId={selected?.raw.id ?? null} />
          </div>
          {selected && <ExtractPanel row={selected} onChanged={load} />}
        </div>
      )}
    </>
  );
}

type View =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ok"; data: OneClickData };

async function runAll(current: Run | null): Promise<{ run: Run; data: OneClickData }> {
  // ① 이번 주 실행: 있으면 그것을, 없으면 새로 만든다
  const run = current ?? (await getLatestRun()) ?? (await createRun());
  // ② 수집: sources.json에서 켜져 있고 수동이 아닌 출처만 (법령은 ④에서)
  const settings = await getSources();
  const names = new Map(settings.map((s) => [s.id, s.name]));
  const ids = settings.filter((s) => s.enabled && s.mode !== "manual" && s.id !== "law_api").map((s) => s.id);
  const collected = ids.length > 0 ? await collect(run.id, ids) : [];
  // ③ 선별 → 추출 → 고객사 판단
  await analyze(run.id);
  // ④ 법령 개정
  const law = await fetchLaw(run.id);
  // ⑤ 결과 읽기
  const [items, matches, laws, customers] = await Promise.all([
    getItems(run.id),
    getMatches(run.id),
    getLaw(run.id),
    getCustomers(),
  ]);
  const failed = [
    ...collected
      .filter((c) => c.status === "failed")
      .map((c) => `${names.get(c.source) ?? c.source}(${c.message})`),
    ...law.errors.map((e) => `${TEXT.lawSource}(${e})`),
  ];
  return { run, data: { items, matches, laws, customers, failed } };
}

function errorText(e: unknown): string {
  return e instanceof Error ? e.message : TEXT.unknownError;
}

function draftsByCustomer(drafts: MailDraft[]): Record<string, DraftState> {
  const out: Record<string, DraftState> = {};
  for (const d of drafts) {
    if (d.kind === "customer" && d.customer_id) out[d.customer_id] = { kind: "ok", draft: d };
  }
  return out;
}

// 맨 위 넓은 상자: 두 칸을 가로로 다 쓰고, 높이는 고객사 카드의 1.5배.
function SelectBox({ run, view, onRun }: { run: Run | null; view: View; onRun: () => void }) {
  const done = view.kind === "ok";
  const footer = [run ? `${run.week_label} (${run.period_start} ~ ${run.period_end})` : TEXT.notRun, done ? TEXT.aiNote : ""]
    .filter(Boolean)
    .join(" · ");
  return (
    <BoardCard
      tag={TEXT.selectTag}
      icon="🔎"
      title={TEXT.selectTitle}
      help={<HelpTip lines={TEXT.selectHelp} />}
      footer={footer}
      style={{ gridColumn: "1 / -1", minHeight: CARD_HEIGHT * 1.5 }}
    >
      <p style={{ margin: 0, color: color.muted }}>{TEXT.selectDesc}</p>
      <InnerBox style={{ display: "flex", flexWrap: "wrap", gap: space.sm, alignItems: "center" }}>
        {TEXT.steps.map((step, i) => (
          <span key={step} style={{ display: "inline-flex", alignItems: "center", gap: space.xs }}>
            {i > 0 && <span style={{ color: color.muted }}>→</span>}
            <span
              style={{
                padding: "1px 8px",
                borderRadius: 6,
                background: color.surface,
                border: `1px solid ${color.border}`,
                color: done ? color.success : color.text,
              }}
            >
              <small>{done ? `✔ ${step}` : step}</small>
            </span>
          </span>
        ))}
      </InnerBox>
      {view.kind === "loading" && <Loading />}
      {view.kind === "error" && <ErrorState message={view.message} onRetry={onRun} />}
      {view.kind === "ok" && view.data.failed.length > 0 && (
        <ErrorState message={`${TEXT.failedSources}: ${view.data.failed.join(", ")}`} />
      )}
      <button
        type="button"
        className="primary"
        disabled={view.kind === "loading"}
        onClick={onRun}
        style={{ width: "100%", marginTop: "auto" }}
      >
        {done ? TEXT.rerun : TEXT.runAll}
      </button>
    </BoardCard>
  );
}

export default function CollectPage() {
  const [run, setRun] = useState<Run | null>(null);
  const [view, setView] = useState<View>({ kind: "idle" });
  const [customers, setCustomers] = useState<CustomerSetting[]>([]);
  const [drafts, setDrafts] = useState<Record<string, DraftState>>({});
  const [detailsKey, setDetailsKey] = useState(0);

  useEffect(() => {
    Promise.all([getLatestRun(), getCustomers()])
      .then(([r, cs]) => {
        setRun(r);
        setCustomers(cs);
      })
      .catch((e: unknown) => setView({ kind: "error", message: errorText(e) }));
  }, []);

  async function onRun() {
    setView({ kind: "loading" });
    try {
      const res = await runAll(run);
      setRun(res.run);
      setCustomers(res.data.customers);
      setView({ kind: "ok", data: res.data });
      setDetailsKey((k) => k + 1);
      const existing = await getDrafts(res.run.id).catch((): MailDraft[] => []);
      setDrafts(draftsByCustomer(existing));
    } catch (e) {
      setView({ kind: "error", message: errorText(e) });
    }
  }

  async function onMake(customerId: string) {
    if (!run) return;
    setDrafts((d) => ({ ...d, [customerId]: { kind: "busy" } }));
    let next: DraftState;
    try {
      // B2-03에는 고객사 하나만 만드는 API가 없어, 전체를 만든 뒤 이 고객사 초안만 꺼낸다.
      const all = await makeDrafts(run.id);
      const found = all.find((x) => x.kind === "customer" && x.customer_id === customerId);
      next = found ? { kind: "ok", draft: found } : { kind: "error", message: TEXT.noDraftForCustomer };
    } catch (e) {
      next = { kind: "error", message: errorText(e) };
    }
    setDrafts((d) => ({ ...d, [customerId]: next }));
  }

  const ready = view.kind === "ok";
  const lines = view.kind === "ok" ? buildLines(view.data).lines : [];

  return (
    <>
      <h1 style={{ margin: `0 0 ${space.md}px`, fontSize: 22 }}>{TEXT.title}</h1>
      <AiStatusBar usage={TEXT.aiUsage} />
      <div
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(2, minmax(0, ${CARD_WIDTH}px))`,
          columnGap: 44,
          rowGap: 40,
          padding: space.lg,
          background: color.background,
          border: `1px solid ${color.border}`,
          borderRadius: 16,
          width: "fit-content",
          maxWidth: "100%",
        }}
      >
        <SelectBox run={run} view={view} onRun={onRun} />
        {customers.length === 0 && view.kind !== "error" && (
          <div style={{ gridColumn: "1 / -1" }}>
            <EmptyState message={TEXT.noCustomers} />
          </div>
        )}
        {customers.map((c) => (
          <CustomerCard
            key={c.customer_id}
            customer={c}
            lines={lines.filter((l) => l.customers.some((x) => x.id === c.customer_id))}
            ready={ready}
            draft={drafts[c.customer_id] ?? { kind: "none" }}
            onMake={() => void onMake(c.customer_id)}
          />
        ))}
      </div>

      {view.kind === "ok" && (
        <details style={{ marginTop: space.lg }}>
          <summary>{TEXT.allResults}</summary>
          <OneClickResult data={view.data} />
        </details>
      )}
      {run && (
        <details style={{ marginTop: space.md }}>
          <summary style={{ color: color.muted }}>{TEXT.details}</summary>
          <div style={{ marginTop: space.md }}>
            <CollectBody key={detailsKey} run={run} />
          </div>
        </details>
      )}
    </>
  );
}
