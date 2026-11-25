"use client";
// B1-09 원문·추출 정보 수정 + 선별 바꾸기 (LSH)
import { useEffect, useState } from "react";
import { Badge } from "../../../components/ui/Badge";
import { color } from "../../../components/ui/tokens";
import { setLabel } from "../../../lib/api/b1/classify";
import { saveExtracted } from "../../../lib/api/b1/extract";
import type { ExtractedPatch, ItemRow } from "../../../lib/types/b1";
import type { Label } from "../../../lib/types/core";

const FIELDS: { key: keyof ExtractedPatch; label: string }[] = [
  { key: "product_name_ko", label: "제품명" },
  { key: "product_name_en", label: "제품명(영문)" },
  { key: "food_type_raw", label: "식품유형" },
  { key: "origin_country", label: "원산지(제조국)" },
  { key: "maker", label: "제조·수출회사" },
  { key: "hs_code", label: "HS 코드" },
  { key: "violation", label: "위반 내역" },
  { key: "period_start", label: "기간 시작" },
  { key: "period_end", label: "기간 끝" },
];

export function ExtractPanel({ row, onChanged }: { row: ItemRow; onChanged: () => void }) {
  const [form, setForm] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    const e = row.extracted;
    setForm(Object.fromEntries(FIELDS.map((f) => [f.key, e ? String(e[f.key] ?? "") : ""])));
    setMsg(null);
  }, [row]);

  async function label(l: Label) {
    setMsg("아래 단계 다시 실행 중…");
    try {
      await setLabel(row.raw.id, l);
      onChanged();
      setMsg("저장했습니다.");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "저장 실패");
    }
  }

  async function save() {
    const e = row.extracted;
    const patch: Record<string, string | null> = {};
    for (const f of FIELDS) {
      const before = e ? String(e[f.key] ?? "") : "";
      if (form[f.key] !== before) patch[f.key] = form[f.key] || null;
    }
    if (Object.keys(patch).length === 0) return;
    setMsg("아래 단계 다시 실행 중…");
    try {
      await saveExtracted(row.raw.id, patch as ExtractedPatch);
      onChanged();
      setMsg("저장했습니다. 고객사 판단을 다시 했습니다.");
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "저장 실패");
    }
  }

  const edited = row.extracted?.edited_fields ?? [];
  return (
    <aside style={{ width: 380, padding: 16, background: color.surface, border: `1px solid ${color.border}` }}>
      <h3 style={{ marginTop: 0 }}>{row.raw.title}</h3>
      <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, background: color.background, padding: 8, maxHeight: 160, overflow: "auto" }}>
        {row.raw.body || "(본문 없음)"}
      </pre>
      <div style={{ display: "flex", gap: 8, margin: "8px 0" }}>
        <button type="button" onClick={() => label("relevant")}>관련</button>
        <button type="button" onClick={() => label("irrelevant")}>무관</button>
        <button type="button" onClick={() => label("review_needed")}>검토 필요</button>
      </div>
      {row.selection && (row.selection.final_label ?? row.selection.ai_label) !== "irrelevant" && (
        <>
          <h4>추출 정보 {row.extracted ? "" : "(분석 전)"}</h4>
          {FIELDS.map((f) => (
            <label key={f.key} style={{ display: "block", marginBottom: 6, fontSize: 13 }}>
              {f.label} {edited.includes(f.key) && <Badge tone="warning">담당자 수정</Badge>}
              <input
                value={form[f.key] ?? ""}
                placeholder="확인 필요"
                onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
                style={{ display: "block", width: "100%", boxSizing: "border-box" }}
              />
            </label>
          ))}
          <button type="button" onClick={save}>추출 칸 저장</button>
        </>
      )}
      {msg && <p style={{ color: color.muted }}>{msg}</p>}
    </aside>
  );
}
