"use client";
// B2-01 보고서 미리보기 (KHW).
// - 발송할 본문(report.text)과 b1에서 정리할 것(report.check)을 나눠 보여 준다.
//   check는 화면 전용이라 메일 초안에 들어가지 않는다. 확인·확정은 b1 화면에서 한다.
// - [본문 복사]는 본문(report.text)만 복사한다.
// - 섹션 2 재안내 글을 저장하면 보고서를 다시 조립해 이 상자에 보여 준다 (page.tsx는 그대로).
import { useState } from "react";
import { AiBadge, Badge } from "../../../components/ui/Badge";
import { color } from "../../../components/ui/tokens";
import { buildReport, setReannounce } from "../../../lib/api/b2/report";
import type { ReportOut } from "../../../lib/types/b2";

const TEXT = {
  title: "주간 보고서",
  bodyLabel: "발송할 본문",
  checkLabel: "⚠ b1에서 정리할 것 · 메일에 들어가지 않음",
  checkHelp:
    "이 목록은 메일 초안에 들어가지 않아요. 수집·선별, 고객사 판단 화면에서 정리한 뒤 [보고서 조립]을 다시 눌러 주세요.",
  checkWarn: "⚠ b1에서 정리할 것이 있어요. 아래 주황 상자를 확인해 주세요.",
  noCheck: "정리할 것이 없습니다.",
  copy: "본문 복사",
  copied: "본문을 복사했어요.",
  copyFailed: "복사하지 못했어요. 본문을 직접 선택해 복사해 주세요.",
  counts: (s1: number, s2: number, review: number) =>
    `부적합·검사지시 ${s1}건 · 법령 개정 ${s2}건 · 검토 필요 ${review}건`,
  reannounce: "법령 재안내 (섹션 2)",
  reannounceHelp:
    "새로 시행된 개정이 없는 주에만 섹션 2에 들어갑니다. 고시명·번호·조항·시행일·출처 링크를 함께 적어 주세요.",
  reannouncePlaceholder: "예) 「○○ 고시」 제2026-00호 (시행 2026-00-00) 주요 내용 …\n출처: https://…",
  save: "섹션 2에 넣기",
  clear: "빼기",
  saved: "저장하고 보고서를 다시 조립했어요.",
  failed: "저장하지 못했어요",
};

function mmdd(iso: string): string {
  return `${iso.slice(5, 7)}/${iso.slice(8, 10)}`;
}

const preStyle = { whiteSpace: "pre-wrap", fontSize: 13, margin: 0 } as const;

export function ReportPreview({ report }: { report: ReportOut }) {
  // 재안내 저장 뒤 다시 조립한 보고서. 부모가 새 report를 주면(base가 바뀌면) 그쪽을 쓴다.
  const [local, setLocal] = useState<{ base: ReportOut; value: ReportOut } | null>(null);
  const shown = local && local.base === report ? local.value : report;
  const [text, setText] = useState("");
  const [note, setNote] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const r = shown.report;
  const body = shown.text;
  const check = shown.check ?? "";

  async function copyBody() {
    try {
      await navigator.clipboard.writeText(body);
      setNote(TEXT.copied);
    } catch {
      // 클립보드 권한이 없는 화면(내장 브라우저 등)에서는 숨긴 입력칸을 골라 복사한다.
      const area = document.createElement("textarea");
      area.value = body;
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.select();
      const ok = document.execCommand("copy");
      document.body.removeChild(area);
      setNote(ok ? TEXT.copied : TEXT.copyFailed);
    }
  }

  async function saveReannounce(value: string | null) {
    setBusy(true);
    setNote(null);
    try {
      await setReannounce(r.run_id, value);
      setLocal({ base: report, value: await buildReport(r.run_id) });
      if (value === null) setText("");
      setNote(TEXT.saved);
    } catch (e) {
      setNote(`${TEXT.failed}: ${e instanceof Error ? e.message : ""}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section style={{ background: color.card, borderRadius: 20, padding: 20, marginBottom: 16 }}>
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8 }}>
        <strong style={{ fontSize: 16 }}>
          {TEXT.title} · {r.week_label} ({mmdd(r.period_start)}~{mmdd(r.period_end)})
        </strong>
        <AiBadge />
        <button type="button" onClick={copyBody} style={{ marginLeft: "auto" }}>
          {TEXT.copy}
        </button>
      </div>
      <p style={{ margin: "6px 0 12px", color: color.muted, fontSize: 14 }}>
        {TEXT.counts(r.section1_items.length, r.section2_items.length, shown.review_needed)}
      </p>
      {check && <p style={{ margin: "0 0 12px", color: color.warning, fontWeight: 700, fontSize: 14 }}>{TEXT.checkWarn}</p>}
      {note && <p role="status" style={{ margin: "0 0 12px", fontSize: 14 }}>{note}</p>}

      <div aria-label={TEXT.bodyLabel} style={{ background: color.surface, borderRadius: 14, padding: 16 }}>
        <div style={{ marginBottom: 8 }}>
          <Badge tone="muted">{TEXT.bodyLabel}</Badge>
        </div>
        <pre style={preStyle}>{body}</pre>
      </div>

      <div
        aria-label={TEXT.checkLabel}
        style={{
          marginTop: 12,
          background: color.surface,
          border: `2px solid ${color.warning}`,
          borderRadius: 14,
          padding: 16,
        }}
      >
        <div style={{ marginBottom: 6 }}>
          <Badge tone="warning">{TEXT.checkLabel}</Badge>
        </div>
        <p style={{ margin: "0 0 8px", color: color.muted, fontSize: 13 }}>{TEXT.checkHelp}</p>
        <pre style={preStyle}>{check || TEXT.noCheck}</pre>
      </div>

      <details style={{ marginTop: 12, background: color.surface, padding: 12 }}>
        <summary>{TEXT.reannounce}</summary>
        <p style={{ margin: "8px 0", color: color.muted, fontSize: 13 }}>{TEXT.reannounceHelp}</p>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={4}
          placeholder={TEXT.reannouncePlaceholder}
          style={{ display: "block", width: "100%", boxSizing: "border-box", marginBottom: 8 }}
        />
        <button type="button" className="primary" disabled={busy || !text.trim()} onClick={() => saveReannounce(text.trim())}>
          {TEXT.save}
        </button>{" "}
        <button type="button" disabled={busy} onClick={() => saveReannounce(null)}>
          {TEXT.clear}
        </button>
      </details>
    </section>
  );
}
