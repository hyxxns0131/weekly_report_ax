"use client";
// B1-01 수동 업로드 (LSH): CSV 파일 · 텍스트 붙여넣기 · URL
import { type ChangeEvent, useState } from "react";
import { color } from "../../../components/ui/tokens";
import { upload } from "../../../lib/api/b1/collect";
import type { Source } from "../../../lib/types/core";

const SOURCES: { value: Source; label: string }[] = [
  { value: "impfood_unfit", label: "정보마루 부적합" },
  { value: "impfood_inspection", label: "통관단계 검사지시" },
  { value: "impfood_law_policy", label: "관련법령·정책소식" },
  { value: "mfds_notice", label: "식약처 제개정고시" },
  { value: "gyeongin_newsletter", label: "경인청 뉴스레터" },
  { value: "gmail_inbox", label: "메일(공문)" },
  { value: "manual", label: "기타" },
];

export function UploadPanel({ runId, onDone }: { runId: number; onDone: (msg: string) => void }) {
  const [source, setSource] = useState<Source>("impfood_unfit");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function send(kind: "csv" | "text", content: string, filename?: string) {
    setBusy(true);
    setError(null);
    try {
      const r = await upload(runId, { source, kind, content, url: url || null, filename: filename ?? null });
      setText("");
      setUrl("");
      onDone(`${r.items.length}건 올렸습니다. [분석 실행]을 눌러 주세요.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "업로드 실패");
    } finally {
      setBusy(false);
    }
  }

  async function onFile(e: ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (!f) return;
    if (/\.xlsx?$/i.test(f.name)) {
      setError("엑셀은 아직 읽을 수 없습니다. 엑셀에서 'CSV UTF-8'로 저장해 올려 주세요.");
      return;
    }
    await send("csv", await f.text(), f.name);
  }

  return (
    <fieldset style={{ border: `1px solid ${color.border}`, padding: 12, marginBottom: 16, background: color.surface }}>
      <legend>자료 올리기</legend>
      <label>
        출처{" "}
        <select value={source} onChange={(e) => setSource(e.target.value as Source)} disabled={busy}>
          {SOURCES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </label>{" "}
      <label>
        CSV 파일 <input type="file" accept=".csv,.xlsx,.xls" onChange={onFile} disabled={busy} />
      </label>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="공문·뉴스레터 본문을 붙여 넣으세요. 빈 줄로 나누면 항목이 나뉩니다. 첫 줄은 제목."
        rows={4}
        style={{ display: "block", width: "100%", marginTop: 8, boxSizing: "border-box" }}
      />
      <input
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="원문 링크(URL, 선택)"
        style={{ width: "60%", marginTop: 8 }}
      />{" "}
      <button type="button" disabled={busy || (!text.trim() && !url.trim())} onClick={() => send("text", text)}>
        붙여 넣은 내용 올리기
      </button>
      {error && <p style={{ color: color.danger }}>✖ {error}</p>}
    </fieldset>
  );
}
