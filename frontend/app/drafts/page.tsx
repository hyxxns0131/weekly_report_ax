"use client";
// 보고서·메일 (B2-01~05·07, KHW). DESIGN.md 8장. 자동 발송 없음: 초안 → 승인 → 발송.

import { useCallback, useEffect, useState } from "react";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorState } from "../../components/ui/ErrorState";
import { AiStatusBar } from "../../components/ui/AiStatusBar";
import { RunGate } from "../../components/ui/RunGate";
import { color } from "../../components/ui/tokens";
import { getDrafts, makeDrafts } from "../../lib/api/b2/drafts";
import { buildReport } from "../../lib/api/b2/report";
import { getSendInfo } from "../../lib/api/b2/send";
import type { ReportOut } from "../../lib/types/b2";
import type { MailDraft, Run } from "../../lib/types/core";
import { DraftEditor } from "./_components/DraftEditor";
import { DraftList } from "./_components/DraftList";
import { HistoryPanel } from "./_components/HistoryPanel";
import { ReportPreview } from "./_components/ReportPreview";
import { SendPanel } from "./_components/SendPanel";
import { TipPanel } from "./_components/TipPanel";
import { WarningList } from "./_components/WarningList";

const TEXT = {
  title: "보고서·메일",
  report: "보고서 조립",
  drafts: "메일 초안 만들기",
  empty: "아직 초안이 없습니다. [보고서 조립] → [메일 초안 만들기]를 눌러 주세요.",
  unsaved: "글상자에 저장하지 않은 수정이 있습니다. 넘어가면 그 수정은 사라집니다. 계속할까요?",
  saveFirst: "저장하지 않은 수정이 있습니다. 먼저 [저장]해야 승인·발송할 수 있습니다.",
};

function Body({ run }: { run: Run }) {
  const [report, setReport] = useState<ReportOut | null>(null);
  const [drafts, setDrafts] = useState<MailDraft[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [sendEnabled, setSendEnabled] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  // B2-04: 글상자에 저장하지 않은 수정이 있는지 (DraftEditor가 알려 준다).
  const [dirty, setDirty] = useState(false);

  const load = useCallback(async () => {
    try {
      const d = await getDrafts(run.id);
      setDrafts(d);
      setSelected((s) => s ?? d[0]?.id ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "불러오지 못했습니다");
    }
  }, [run.id]);

  useEffect(() => {
    void load();
    getSendInfo().then((i) => setSendEnabled(i.mail_send_enabled)).catch(() => setSendEnabled(false));
  }, [load]);

  // 저장 안 한 수정이 있을 때 창을 닫거나(새로 고침 포함) 다른 메뉴로 가려 하면 먼저 묻는다.
  useEffect(() => {
    if (!dirty) return;
    const onUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
    };
    const onLinkClick = (e: MouseEvent) => {
      const link = e.target instanceof Element ? e.target.closest("a[href]") : null;
      if (link && !window.confirm(TEXT.unsaved)) {
        e.preventDefault();
        e.stopPropagation();
      }
    };
    window.addEventListener("beforeunload", onUnload);
    document.addEventListener("click", onLinkClick, true);
    return () => {
      window.removeEventListener("beforeunload", onUnload);
      document.removeEventListener("click", onLinkClick, true);
    };
  }, [dirty]);

  function confirmLeave(): boolean {
    return !dirty || window.confirm(TEXT.unsaved);
  }

  function selectDraft(id: number) {
    if (id === selected || !confirmLeave()) return;
    setSelected(id);
  }

  async function act(fn: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : "실패");
    } finally {
      setBusy(false);
    }
  }

  const names = report?.customer_names ?? {};
  const counts = { draft: 0, approved: 0, sent: 0 };
  drafts.forEach((d) => { counts[d.status] += 1; });
  const current = drafts.find((d) => d.id === selected) ?? null;
  const hasCurrent = current !== null;
  useEffect(() => {
    if (!hasCurrent) setDirty(false); // 글상자가 없으면 저장 안 한 수정도 없다
  }, [hasCurrent]);

  return (
    <>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12 }}>
        <button type="button" disabled={busy} onClick={() => act(async () => setReport(await buildReport(run.id)))}>{TEXT.report}</button>
        <button type="button" className="primary" disabled={busy} onClick={() => confirmLeave() && act(async () => {
          setReport(await buildReport(run.id));
          const d = await makeDrafts(run.id);
          setDrafts(d);
          setSelected(d[0]?.id ?? null);
        })}>{TEXT.drafts}</button>
        <span style={{ marginLeft: "auto", color: color.muted }}>상태: 초안 {counts.draft} · 승인 {counts.approved} · 발송 {counts.sent}</span>
      </div>
      {error && <ErrorState message={error} />}
      <TipPanel runId={run.id} onSaved={() => act(async () => setReport(await buildReport(run.id)))} />
      {report && <ReportPreview report={report} />}
      {drafts.length === 0 ? (
        <EmptyState message={TEXT.empty} />
      ) : (
        <div style={{ display: "flex", gap: 16 }}>
          <DraftList drafts={drafts} names={names} selected={selected} onSelect={selectDraft} />
          {current && (
            <div style={{ flex: 1 }}>
              <DraftEditor draft={current} onSaved={load} onDirtyChange={setDirty} />
              <WarningList warnings={current.warnings} />
              {/* 저장 안 한 수정이 있으면 승인·발송을 막는다: 화면 글과 승인되는 글이 달라지지 않게 */}
              {dirty && <p style={{ color: color.warning }}>{TEXT.saveFirst}</p>}
              <fieldset disabled={dirty} style={{ border: 0, padding: 0, margin: 0 }}>
                <SendPanel draft={current} sendEnabled={sendEnabled} onChanged={load} />
              </fieldset>
              <HistoryPanel draft={current} dirty={dirty} onRestored={load} />
            </div>
          )}
        </div>
      )}
    </>
  );
}

export default function DraftsPage() {
  return <RunGate title={TEXT.title} aside={<AiStatusBar usage="메일 초안 문장과 오늘의 팁 작성에 씁니다" />}>
      {(run) => <Body run={run} />}
    </RunGate>;
}
