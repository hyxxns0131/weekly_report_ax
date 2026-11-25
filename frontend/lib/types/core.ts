// 공통 타입 (KHS). backend/app/core/schema.py와 같은 모양으로 유지한다.

export type Source =
  | "impfood_unfit"
  | "impfood_inspection"
  | "impfood_law_policy"
  | "mfds_notice"
  | "gyeongin_newsletter"
  | "law_api"
  | "gmail_inbox"
  | "manual";
export type Label = "relevant" | "irrelevant" | "review_needed";
export type Category = "unfit" | "inspection_order" | "law_change" | "policy_news" | "other";
export type MatchRule = "maker" | "hs_code" | "origin_food_type" | "food_type_parent" | "food_type_only";
export type Confidence = "high" | "medium";
export type Crosscheck = "match" | "api_only" | "notice_only" | "not_checked";
export type ReportStatus = "draft" | "confirmed";
export type MailKind = "staff_summary" | "customer";
export type MailStatus = "draft" | "approved" | "sent";

export interface RawItem {
  id: string;
  run_id: number;
  source: Source;
  title: string;
  body: string;
  posted_at: string | null;
  url: string | null;
  collected_at: string;
}

export interface Selection {
  item_id: string;
  ai_label: Label;
  final_label: Label | null;
  ai_category: Category;
  final_category: Category | null;
  ai_reason: string;
  evidence_quote: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
}

export interface ExtractedInfo {
  item_id: string;
  product_name_ko: string | null;
  product_name_en: string | null;
  food_type_raw: string | null;
  food_type_std: string | null;
  origin_country: string | null;
  export_country: string | null;
  maker: string | null;
  hs_code: string | null;
  violation: string | null;
  action: string | null;
  office: string | null;
  period_start: string | null;
  period_end: string | null;
  edited_fields: string[];
}

export interface CustomerMatch {
  item_id: string;
  customer_id: string;
  ai_matched: boolean;
  final_matched: boolean | null;
  rule: MatchRule;
  confidence: Confidence;
  reason: string;
}

export interface LawChange {
  id: string;
  law_name: string | null;
  kind: string | null;
  change_type: string | null;
  number: string | null;
  promulgated_at: string | null;
  effective_at: string | null;
  articles: string | null;
  ai_summary: string | null;
  final_summary: string | null;
  source_url: string | null;
  crosscheck: Crosscheck;
  crosscheck_note: string;
  related_food_types: string[];
}

export interface SelectedItem {
  raw: RawItem;
  selection: Selection;
  extracted: ExtractedInfo | null;
  matches: CustomerMatch[];
}

export interface WeeklySelection {
  run_id: number;
  period_start: string;
  period_end: string;
  week_label: string;
  items: SelectedItem[];
  law_changes: LawChange[];
}

export interface WeeklyReport {
  run_id: number;
  period_start: string;
  period_end: string;
  week_label: string;
  section1_items: SelectedItem[];
  section2_items: LawChange[];
  section3_tip: string | null;
  status: ReportStatus;
}

export interface MailDraft {
  id: number;
  run_id: number;
  kind: MailKind;
  customer_id: string | null;
  subject: string;
  ai_body: string;
  final_body: string | null;
  warnings: string[];
  status: MailStatus;
  approved_by: string | null;
  approved_at: string | null;
  sent_at: string | null;
  gmail_draft_id: string | null;
  gmail_message_id: string | null;
}

export interface EvalResult {
  run_id: number;
  golden_week: string;
  selection_recall: number | null;
  selection_precision: number | null;
  match_recall: number | null;
  match_precision: number | null;
  review_needed_ratio: number | null;
  missed_items: string[];
  extra_items: string[];
  wrong_matches: string[];
  elapsed_sec: number | null;
}

// ── core API 응답 ──
export interface Health {
  status: string;
  llm_enabled: boolean;
  login_configured: boolean;
}

export interface LoginResponse {
  token: string;
  username: string;
  expires_at: number;
}

export interface Me {
  username: string;
}

export interface Run {
  id: number;
  reference_date: string;
  period_start: string;
  period_end: string;
  week_label: string;
  created_by: string | null;
  created_at: string;
}

// 현황·단계 바 (C-06). backend/app/core/runs/service.py와 같은 모양.
export type StepGroup = "b1" | "b2";
export type StepState = "waiting" | "current" | "done";
// StatusBadge 글자 (○ 대기 ● 진행·확인 중 ✔ 완료 ✖ 실패, DESIGN.md 3-1)
export type StageState = "waiting" | "in_progress" | "done" | "failed";

export interface StepStatus {
  key: string;
  group: StepGroup;
  name: string;
  state: StepState;
  done: boolean;
  note: string;
}

export interface RunCounts {
  raw_items: number;
  collect_failed: number;
  selected: number;
  review_needed: number;
  relevant: number;
  extracted: number;
  empty_fields: number;
  matches: number;
  laws: number;
  law_mismatch: number;
  report_done: boolean;
  drafts: number;
  draft_warnings: number;
  approval_waiting: number;
  approved: number;
  sent: number;
  evaluated: boolean;
}

export interface Todo {
  key: string;
  text: string;
  count: number;
  href: string;
  group: StepGroup;
}

export interface RunStatus {
  run: Run;
  counts: RunCounts;
  steps: StepStatus[];
  current: Record<StepGroup, string | null>;
  materials_ready: boolean;
  todos: Todo[];
}

// 알림 — 이번 주 바뀐 점 (C-06, DESIGN.md 3-2). backend/app/core/runs/notices.py와 같은 모양.
export type NoticeKind = "law_change" | "inspection_order";
export type NoticeAction = "read" | "dismiss";

export interface Notice {
  id: string;
  kind: NoticeKind;
  title: string;
  summary: string | null;
  summary_is_ai: boolean;
  crosscheck: Crosscheck | null;
  effective_at: string | null;
  food_types: string[];
  customers: string[];
  source: string | null;
  url: string | null;
  read_by: string | null;
  read_at: string | null;
}

export interface NoticeList {
  items: Notice[];
  unread: number;
  total: number;
}

// AI 연결 상태 (C-02). backend/app/core/llm.py와 같은 모양. 키 값은 오지 않는다.
export type AiProvider = "openai" | "claude";
export type AiState = "off" | "no_key" | "no_model" | "ready" | "ok" | "error";

export interface AiTest {
  ok: boolean;
  message: string;
  provider: AiProvider;
  model: string;
  checked_at: string;
  elapsed_ms: number;
  available_models: string[];
}

export interface AiStatus {
  enabled: boolean;
  provider: AiProvider;
  provider_label: string;
  model: string;
  key_set: boolean;
  state: AiState;
  state_label: string;
  models: string[];
  providers: AiProvider[];
  last_test: AiTest | null;
}

// 연결 설정 (C-01). 키·토큰 값은 오지 않는다.
export type ConnId = "ai" | "supabase_read" | "supabase_write" | "google_drive" | "gmail" | "law_api";
export type ConnState = "off" | "no_key" | "ready" | "ok" | "error";

export interface ConnTest {
  ok: boolean;
  message: string;
  checked_at: string;
  elapsed_ms: number;
}

export interface ConnStatus {
  id: ConnId;
  name: string;
  usage: string;
  env_names: string[];
  configured: boolean;
  state: ConnState;
  state_label: string;
  hint: string;
  last_test: ConnTest | null;
}
