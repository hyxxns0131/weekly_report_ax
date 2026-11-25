"use client";
// B2-07 오늘의 팁 (KHW, P2). 근거를 확인한 뒤에만 넣는다.
import { useEffect, useState } from "react";
import { color } from "../../../components/ui/tokens";
import { getTopics, setTip } from "../../../lib/api/b2/tips";
import type { TipTopic } from "../../../lib/types/b2";

export function TipPanel({ runId, onSaved }: { runId: number; onSaved: () => void }) {
  const [topics, setTopics] = useState<TipTopic[]>([]);
  const [text, setText] = useState("");
  useEffect(() => {
    getTopics().then(setTopics).catch(() => setTopics([]));
  }, []);
  return (
    <details style={{ marginBottom: 16, background: color.surface, border: `1px solid ${color.border}`, padding: 8 }}>
      <summary>오늘의 팁 (섹션 3)</summary>
      <select onChange={(e) => setText(topics.find((t) => t.id === e.target.value)?.draft ?? "")} defaultValue="">
        <option value="">주제 고르기</option>
        {topics.map((t) => <option key={t.id} value={t.id}>{t.title}</option>)}
      </select>
      <textarea value={text} onChange={(e) => setText(e.target.value)} rows={3} style={{ display: "block", width: "100%", marginTop: 8, boxSizing: "border-box" }} placeholder="근거(법령·고시·공전 항목, 링크)를 확인한 뒤 적어 주세요." />
      <button type="button" onClick={async () => { await setTip(runId, text || null); onSaved(); }}>섹션 3에 넣기</button>{" "}
      <button type="button" onClick={async () => { setText(""); await setTip(runId, null); onSaved(); }}>빼기</button>
    </details>
  );
}
