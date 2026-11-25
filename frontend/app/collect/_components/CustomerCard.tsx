// 고객사 카드 하나 (LSH, /collect 보드). 이번 주 그 고객사 관련 항목 + [메일 초안 만들기].
// 초안은 KHW의 B2-03 API(lib/api/b2/drafts.ts)를 그대로 부른다. 여기서는 보여 주기만 하고 고치기는 /drafts에서.
import Link from "next/link";
import { color, space } from "../../../components/ui/tokens";
import type { CustomerSetting } from "../../../lib/types/b1";
import type { MailDraft } from "../../../lib/types/core";
import { BoardCard, CARD_HEIGHT, InnerBox } from "./BoardCard";
import { HelpTip } from "./HelpTip";
import { type Line, lineTips } from "./OneClickResult";

const TEXT = {
  tag: "고객사",
  waiting: "위에서 [고객사 선별하기]를 먼저 눌러 주세요.",
  none: "이번 주 관련 항목 없음",
  make: "✉ 메일 초안 만들기",
  remake: "✉ 메일 초안 다시 만들기",
  making: "초안 만드는 중…",
  edit: "보고서·메일 화면에서 고치기 →",
  noDraft: "초안 없음",
  ai: "AI 초안 · 담당자 확인 전",
  edited: "담당자 수정본 있음",
  warnings: "경고 있음 · 고치기 화면에서 확인",
  help: (name: string) => [`${name} 관련 항목만 모았습니다.`, "각 줄의 ?에 판단 근거가 있습니다."],
};

export type DraftState =
  | { kind: "none" }
  | { kind: "busy" }
  | { kind: "error"; message: string }
  | { kind: "ok"; draft: MailDraft };

export function CustomerCard({
  customer,
  lines,
  ready,
  draft,
  onMake,
}: {
  customer: CustomerSetting;
  lines: Line[];
  ready: boolean;
  draft: DraftState;
  onMake: () => void;
}) {
  const id = customer.customer_id;
  const busy = draft.kind === "busy";
  const has = draft.kind === "ok";
  const footer =
    draft.kind === "ok"
      ? [draft.draft.final_body ? TEXT.edited : TEXT.ai, draft.draft.warnings.length > 0 ? TEXT.warnings : ""]
          .filter(Boolean)
          .join(" · ")
      : busy
        ? TEXT.making
        : TEXT.noDraft;

  return (
    <BoardCard
      tag={TEXT.tag}
      icon="🏢"
      title={customer.display_name}
      help={<HelpTip lines={TEXT.help(customer.display_name)} />}
      footer={footer}
      style={{ minHeight: CARD_HEIGHT }}
    >
      {!ready && <p style={{ margin: 0, color: color.muted }}><small>{TEXT.waiting}</small></p>}
      {ready && lines.length === 0 && <p style={{ margin: 0, color: color.muted }}><small>{TEXT.none}</small></p>}
      {ready && lines.length > 0 && (
        <InnerBox style={{ maxHeight: 112, overflowY: "auto" }}>
          {lines.map((l) => {
            const strong = l.customers.some((c) => c.id === id && c.strong);
            return (
              <div key={l.key} style={{ display: "flex", alignItems: "center", gap: space.xs, padding: "2px 0" }}>
                <small style={{ fontWeight: 700, whiteSpace: "nowrap" }}>{l.tag}</small>
                <small
                  style={{ flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontWeight: strong ? 700 : 400 }}
                  title={l.text}
                >
                  {l.text}
                </small>
                <HelpTip lines={lineTips(l, id)} />
              </div>
            );
          })}
        </InnerBox>
      )}

      {draft.kind === "ok" && (
        <InnerBox>
          <small style={{ display: "block", fontWeight: 700 }}>{draft.draft.subject}</small>
          <small
            style={{
              display: "-webkit-box",
              WebkitLineClamp: 3,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
              whiteSpace: "pre-line",
              color: color.muted,
            }}
          >
            {draft.draft.final_body ?? draft.draft.ai_body}
          </small>
          <small>
            <Link href="/drafts/">{TEXT.edit}</Link>
          </small>
        </InnerBox>
      )}
      {draft.kind === "error" && (
        <p role="alert" style={{ margin: 0, color: color.danger }}>
          <small>✖ {draft.message}</small>
        </p>
      )}

      <button
        type="button"
        onClick={onMake}
        disabled={!ready || lines.length === 0 || busy}
        style={{ width: "100%", marginTop: "auto" }}
      >
        {busy ? TEXT.making : has ? TEXT.remake : TEXT.make}
      </button>
    </BoardCard>
  );
}
