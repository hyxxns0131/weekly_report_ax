// B2-02~04 초안 목록 (KHW)
import { Badge } from "../../../components/ui/Badge";
import { color } from "../../../components/ui/tokens";
import type { MailDraft } from "../../../lib/types/core";

// 백엔드 b2_mail/draft/customer.py DROPPED_MARK와 같게 둔다
const DROPPED_MARK = "[대상 제외]";
const DROPPED_BADGE = "대상 제외 · 보내지 마세요";

/** 다시 만들 때 이번 주 안내 대상에서 빠진 고객사 초안. 승인할 수 없다. */
export function isDropped(d: MailDraft): boolean {
  return d.warnings.some((w) => w.startsWith(DROPPED_MARK));
}

export function draftName(d: MailDraft, names: Record<string, string>): string {
  return d.kind === "staff_summary" ? "담당자용 요약" : `${names[d.customer_id ?? ""] ?? d.customer_id} 안내`;
}

export function StatusOf({ d }: { d: MailDraft }) {
  if (d.status === "sent") return <Badge tone="success">발송됨</Badge>;
  if (isDropped(d)) return <Badge tone="danger">{DROPPED_BADGE}</Badge>;
  if (d.status === "approved") return <Badge tone="muted">승인됨</Badge>;
  return d.final_body ? <Badge tone="warning">초안 · 담당자 수정</Badge> : <Badge tone="info">AI 결과 · 담당자 확인 전</Badge>;
}

export function DraftList({ drafts, names, selected, onSelect }: {
  drafts: MailDraft[];
  names: Record<string, string>;
  selected: number | null;
  onSelect: (id: number) => void;
}) {
  return (
    <nav style={{ width: 200, borderRight: `1px solid ${color.border}`, paddingRight: 8 }}>
      {drafts.map((d) => (
        <button key={d.id} type="button" onClick={() => onSelect(d.id)}
          style={{ display: "block", width: "100%", textAlign: "left", padding: 8, marginBottom: 4, fontWeight: d.id === selected ? 700 : 400,
            color: isDropped(d) ? color.muted : undefined, textDecoration: isDropped(d) ? "line-through" : undefined }}>
          ▸ {draftName(d, names)}
          <div><StatusOf d={d} /></div>
        </button>
      ))}
    </nav>
  );
}
