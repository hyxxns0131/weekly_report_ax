// b2 화면 타입 (KHW).
import type { WeeklyReport } from "./core";

export interface ReportOut {
  report: WeeklyReport;
  text: string; // 메일로 나가는 본문만
  review_needed: number;
  customer_names: Record<string, string>;
  check: string; // 화면 전용 확인 목록 (메일 초안에 넣지 않음). 없으면 ""
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
  staff_to_count: number; // 담당자용 받는 사람 수 (주소는 화면에 오지 않는다)
  body_format: string; // "html" | "text"
}
