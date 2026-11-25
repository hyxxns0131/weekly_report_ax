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

export type StageState = "waiting" | "in_progress" | "done" | "failed";

export interface StageStatus {
  key: string;
  name: string;
  status: StageState;
  count: number;
}

export interface RunStatus {
  run: Run;
  stages: StageStatus[];
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
