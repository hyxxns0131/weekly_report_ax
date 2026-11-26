// 버튼 하나 데모 뷰: 결과를 번호 목록 하나로 (LSH, B1-01~11 + B1-12·13 화면 묶음).
// 표·탭 없이 한 줄씩. 이유·근거는 ? 말풍선에만 둔다. 점수·숫자·영문 규칙 이름은 보여 주지 않는다.
import { color, space } from "../../../components/ui/tokens";
import type { CustomerSetting, ItemRow, MatchRow, OneClickData } from "../../../lib/types/b1";
import type { Category, LawChange, MatchRule } from "../../../lib/types/core";
import { HelpTip } from "./HelpTip";
import { MATCH_RULE_GUIDE, selectRuleGuide } from "./ruleGuide";

const TEXT = {
  aiNote: "AI 결과 · 담당자 확인 전",
  noCustomer: "관련 고객사 없음",
  review: "확인 필요",
  reviewTip: "담당자 확인 필요",
  irrelevant: (n: number) => `무관 ${n}건`,
  lawTag: "[법령]",
  lawReason: "새로 시행된 법령 개정",
  lawFoodTypes: "본문 식품유형",
  lawNoFoodType: "본문에서 고객사 식품유형을 찾지 못함",
  effective: (mmdd: string) => `시행 ${mmdd}`,
  empty: "이번 주 수입식품 관련 항목이 없습니다.",
  tags: {
    unfit: "[부적합]",
    inspection_order: "[검사지시]",
    law_change: "[법령]",
    policy_news: "[정책]",
    other: "[기타]",
  } satisfies Record<Category, string>,
  rules: {
    maker: "같은 제조사",
    hs_code: "HS 코드",
    origin_food_type: "원산지+식품유형",
    food_type_parent: "원산지+상위 식품유형",
    food_type_only: "식품유형만",
  } satisfies Record<MatchRule, string>,
};

// 한 줄에 걸린 고객사. tip은 그 고객사 근거 한 줄 (? 말풍선용).
export type LineCustomer = { id: string; name: string; strong: boolean; tip: string; guide: string };
export type Line = {
  key: string;
  tag: string;
  review: boolean;
  text: string;
  customers: LineCustomer[];
  reason: string; // 선별 이유 (ai_reason 또는 법령 안내)
};

export function lineTips(l: Line, only?: string): string[] {
  const cs = only ? l.customers.filter((c) => c.id === only) : l.customers;
  return [
    l.reason,
    selectRuleGuide(l.reason),
    ...cs.map((c) => c.tip),
    ...cs.map((c) => c.guide),
    ...(l.review ? [TEXT.reviewTip] : []),
  ].filter((t) => t.length > 0);
}

function mmdd(iso: string | null): string {
  return iso ? `${iso.slice(5, 7)}/${iso.slice(8, 10)}` : "확인 필요";
}

function summary(row: ItemRow, category: Category): string {
  const e = row.extracted;
  if (!e || (category !== "unfit" && category !== "inspection_order")) return row.raw.title;
  const parts = [e.origin_country, e.food_type_raw ?? e.product_name_ko, e.violation].filter(
    (p): p is string => Boolean(p),
  );
  return parts.length >= 2 ? parts.join(" · ") : row.raw.title;
}

function itemLines(items: ItemRow[], matches: MatchRow[]): { lines: Line[]; irrelevant: ItemRow[] } {
  const withCustomer: Line[] = [];
  const noCustomer: Line[] = [];
  const review: Line[] = [];
  const irrelevant: ItemRow[] = [];
  for (const row of items) {
    const sel = row.selection;
    if (!sel) continue;
    const label = sel.final_label ?? sel.ai_label;
    if (label === "irrelevant") {
      irrelevant.push(row);
      continue;
    }
    const category = sel.final_category ?? sel.ai_category;
    const mine = matches.filter((m) => m.item_id === row.raw.id && (m.final_matched ?? m.ai_matched));
    const isReview = label === "review_needed";
    const line: Line = {
      key: row.raw.id,
      tag: TEXT.tags[category],
      review: isReview,
      text: summary(row, category),
      customers: mine.map((m) => ({
        id: m.customer_id,
        name: m.customer_name,
        strong: m.rule === "maker",
        tip: `${TEXT.rules[m.rule]} · ${m.reason}`,
        guide: MATCH_RULE_GUIDE[m.rule] ?? "",
      })),
      reason: sel.ai_reason,
    };
    if (isReview) review.push(line);
    else if (line.customers.length > 0) withCustomer.push(line);
    else noCustomer.push(line);
  }
  return { lines: [...withCustomer, ...noCustomer, ...review], irrelevant };
}

function lawLines(laws: LawChange[], customers: CustomerSetting[]): Line[] {
  return laws.map((law) => {
    const hits = customers
      .map((c) => ({ c, food: law.related_food_types.find((f) => c.keywords.some((k) => k.food_type === f)) }))
      .filter((x): x is { c: CustomerSetting; food: string } => x.food !== undefined);
    const title = [law.law_name ?? "법령명 확인 필요", law.change_type].filter(Boolean).join(" ");
    return {
      key: law.id,
      tag: TEXT.lawTag,
      review: false,
      text: `${title} (${TEXT.effective(mmdd(law.effective_at))})`,
      customers: hits.map((h) => ({
        id: h.c.customer_id,
        name: h.c.display_name,
        strong: false,
        tip: `${TEXT.rules.food_type_only} · 본문에 '${h.food}' 언급 (${h.c.display_name}) · 검토 필요`,
        guide: MATCH_RULE_GUIDE.food_type_only,
      })),
      reason: hits.length > 0 ? TEXT.lawReason : `${TEXT.lawReason} · ${TEXT.lawNoFoodType}`,
    };
  });
}

/** 결과 전체를 순서대로 한 줄씩: 관련(고객사 있음) → 관련(고객사 없음) → 검토 필요 → 법령. */
export function buildLines(data: OneClickData): { lines: Line[]; irrelevant: ItemRow[] } {
  const { lines, irrelevant } = itemLines(data.items, data.matches);
  return { lines: [...lines, ...lawLines(data.laws, data.customers)], irrelevant };
}

function CustomerNames({ customers }: { customers: LineCustomer[] }) {
  if (customers.length === 0) return <span style={{ color: color.muted }}>{TEXT.noCustomer}</span>;
  return (
    <span>
      {customers.map((c, i) => (
        <span key={c.id}>
          {i > 0 && ", "}
          {c.strong ? <strong>{c.name}</strong> : c.name}
        </span>
      ))}
    </span>
  );
}

export function OneClickResult({ data }: { data: OneClickData }) {
  const { lines, irrelevant } = buildLines(data);
  const row = {
    display: "flex",
    alignItems: "center",
    gap: space.sm,
    padding: `${space.sm}px ${space.md}px`,
    borderBottom: `1px solid ${color.border}`,
  } as const;

  return (
    <section style={{ background: color.surface, border: `1px solid ${color.border}`, marginTop: space.md }}>
      <p style={{ margin: 0, padding: `${space.xs}px ${space.md}px`, color: color.info }}>
        <small>{TEXT.aiNote}</small>
      </p>
      {lines.length === 0 && <p style={{ ...row, color: color.muted }}>{TEXT.empty}</p>}
      <ol style={{ margin: 0, padding: 0, listStyle: "none" }}>
        {lines.map((l, i) => (
          <li key={l.key} style={row}>
            <span style={{ minWidth: 28, color: color.muted }}>{i + 1}.</span>
            <span style={{ fontWeight: 700, whiteSpace: "nowrap" }}>{l.tag}</span>
            {l.review && (
              <small style={{ color: color.warning, whiteSpace: "nowrap" }}>{TEXT.review}</small>
            )}
            <span style={{ flex: 1 }}>{l.text}</span>
            <CustomerNames customers={l.customers} />
            <HelpTip lines={lineTips(l)} />
          </li>
        ))}
      </ol>
      {irrelevant.length > 0 && (
        <div style={{ ...row, borderBottom: "none", color: color.muted }}>
          <span style={{ flex: 1 }}>{TEXT.irrelevant(irrelevant.length)}</span>
          <HelpTip
            lines={irrelevant.map((r) => `${r.raw.title} — ${r.selection?.ai_reason ?? ""}`)}
          />
        </div>
      )}
    </section>
  );
}
