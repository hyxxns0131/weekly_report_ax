// b1 화면 타입 (LSH). 공통 모양은 core.ts에서 가져온다.
import type { CustomerMatch, ExtractedInfo, LawChange, RawItem, Selection, Source } from "./core";

export interface CollectResult {
  source: string;
  status: "ok" | "failed" | "manual" | "off";
  items: RawItem[];
  message: string;
}

export interface SourceStatus {
  source: string;
  name: string;
  status: "ok" | "failed" | "manual" | "off" | "waiting";
  count: number;
  message: string;
  at: string | null;
}

export interface ItemRow {
  raw: RawItem;
  selection: Selection | null;
  extracted: ExtractedInfo | null;
}

export interface UploadRequest {
  source: Source;
  kind: "csv" | "text" | "url";
  content: string;
  url?: string | null;
  filename?: string | null;
}

export interface AnalyzeResult {
  total: number;
  relevant: number;
  review_needed: number;
  irrelevant: number;
  matches: number;
}

export interface MatchRow extends CustomerMatch {
  customer_name: string;
  item_title: string;
  item_url: string | null;
}

export interface LawFetchResult {
  window_start: string;
  window_end: string;
  found: number;
  added: number;
  errors: string[];
}

export interface SourceSetting {
  id: string;
  name: string;
  enabled: boolean;
  mode: string;
  section: number;
  allowed: string;
}

export interface CustomerSetting {
  customer_id: string;
  display_name: string;
  keywords: { origin_country: string | null; food_type: string }[];
  makers: string[];
  hs_codes: string[];
}

export type ExtractedPatch = Partial<Omit<ExtractedInfo, "item_id" | "edited_fields">>;

// /collect 데모 뷰: 버튼 하나로 모은 결과 (화면 안에서만 쓴다, 새 API 아님)
export interface OneClickData {
  items: ItemRow[];
  matches: MatchRow[];
  laws: LawChange[];
  customers: CustomerSetting[];
  failed: string[];
}
