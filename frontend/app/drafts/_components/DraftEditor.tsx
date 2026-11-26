"use client";
// B2-04 본문 수정·저장·복사 (KHW). AI 초안과 수정본 나란히 보기.
import { useEffect, useState } from "react";
import { color } from "../../../components/ui/tokens";
import { saveDraft } from "../../../lib/api/b2/drafts";
import type { MailDraft } from "../../../lib/types/core";

const TEXT = {
  saved: "저장했습니다.",
  savedRevoked: "저장했습니다. 본문이 바뀌어 승인이 풀렸습니다.",
  unchanged: "바뀐 내용이 없어 저장하지 않았습니다.",
  failed: "저장하지 못했습니다",
  loadedAi: "AI 초안을 글상자에 불러왔습니다. [저장]을 눌러야 반영됩니다.",
};

export function DraftEditor({ draft, onSaved }: { draft: MailDraft; onSaved: () => void }) {
  const [body, setBody] = useState("");
  const [side, setSide] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  useEffect(() => {
    setBody(draft.final_body ?? draft.ai_body);
    setMsg(null);
  }, [draft]);

  return (
    <div>
      <p><strong>제목:</strong> {draft.subject}</p>
      <label><input type="checkbox" checked={side} onChange={(e) => setSide(e.target.checked)} /> AI 초안 나란히 보기</label>
      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        {side && <pre style={{ flex: 1, whiteSpace: "pre-wrap", fontSize: 13, background: color.background, padding: 8, margin: 0 }}>{draft.ai_body}</pre>}
        <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={24} style={{ flex: 1, fontFamily: "inherit", fontSize: 13 }} />
      </div>
      <button type="button" disabled={draft.status === "sent"} onClick={async () => {
        if (body === (draft.final_body ?? draft.ai_body)) {
          setMsg(TEXT.unchanged);
          return;
        }
        try {
          await saveDraft(draft.id, body);
          setMsg(draft.status === "approved" ? TEXT.savedRevoked : TEXT.saved);
          onSaved();
        } catch (e) {
          setMsg(`${TEXT.failed}: ${e instanceof Error ? e.message : ""}`);
        }
      }}>저장</button>{" "}
      <button type="button" disabled={draft.status === "sent" || body === draft.ai_body} onClick={() => {
        setBody(draft.ai_body);
        setMsg(TEXT.loadedAi);
      }}>AI 초안 불러오기</button>{" "}
      <button type="button" onClick={async () => { await navigator.clipboard.writeText(body); setMsg("본문을 복사했습니다."); }}>복사</button>
      {msg && <span style={{ color: color.muted, marginLeft: 8 }}>{msg}</span>}
    </div>
  );
}
