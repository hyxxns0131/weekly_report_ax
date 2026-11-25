"use client";
// B1-13 요지 수정·관련 식품유형 (LSH)
import { useEffect, useState } from "react";
import { color } from "../../../components/ui/tokens";
import { saveLaw } from "../../../lib/api/b1/law";
import type { LawChange } from "../../../lib/types/core";

export function LawDetail({ law, onSaved }: { law: LawChange; onSaved: () => void }) {
  const [summary, setSummary] = useState("");
  const [types, setTypes] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  useEffect(() => {
    setSummary(law.final_summary ?? law.ai_summary ?? "");
    setTypes(law.related_food_types.join(", "));
    setMsg(null);
  }, [law]);

  async function save() {
    await saveLaw(law.id, {
      final_summary: summary,
      related_food_types: types.split(",").map((t) => t.trim()).filter(Boolean),
    });
    setMsg("저장했습니다. 보고서·초안을 다시 만들면 반영됩니다.");
    onSaved();
  }

  return (
    <aside style={{ width: 420, padding: 16, background: color.surface, border: `1px solid ${color.border}` }}>
      <h3 style={{ marginTop: 0 }}>「{law.law_name ?? "확인 필요"}」</h3>
      <p style={{ fontSize: 13 }}>
        공포·고시일 {law.promulgated_at ?? "확인 필요"} · 시행일 {law.effective_at ?? "확인 필요"} · {law.crosscheck_note}
      </p>
      <h4>주요 개정 조항 (원문)</h4>
      <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, maxHeight: 160, overflow: "auto", background: color.background, padding: 8 }}>
        {law.articles ?? "확인 필요"}
      </pre>
      <label style={{ display: "block" }}>
        개정 요지 (담당자 확정)
        <textarea value={summary} onChange={(e) => setSummary(e.target.value)} rows={5} style={{ width: "100%", boxSizing: "border-box" }} />
      </label>
      <label style={{ display: "block", marginTop: 8 }}>
        관련 식품유형 (쉼표로)
        <input value={types} onChange={(e) => setTypes(e.target.value)} style={{ width: "100%", boxSizing: "border-box" }} />
      </label>
      <button type="button" onClick={save} style={{ marginTop: 8 }}>저장</button>
      {msg && <p style={{ color: color.muted }}>{msg}</p>}
    </aside>
  );
}
