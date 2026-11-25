// b2 화면 타입 (KHW).
import type { WeeklyReport } from "./core";

export interface ReportOut {
  report: WeeklyReport;
  text: string;
  review_needed: number;
  customer_names: Record<string, string>;
}

export interface DraftHistoryRow {
  edited_by: string;
  edited_at: string;
  body: string;
}

export interface TipTopic {
  id: string;
  title: string;
  basis: string;
  draft: string;
}

export interface SendInfo {
  mail_send_enabled: boolean;
}
