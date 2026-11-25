-- 비공개: 과거 주간 보고서 원문과 관련 화주(B2-06 검증 정답). PM 결정(2026-11-25).
-- RLS 켜고 정책 없음 → publishable 키(anon)로는 읽기·쓰기 불가. secret 키(PM)로만 사용.
-- 화주는 보고서에 적힌 가명 표기만 둔다. 공개 표(pub_*)와 섞지 않는다.

create table if not exists public.past_report (
  id            text primary key,          -- 예: 2026-11w4
  week_label    text not null,
  period_start  date,
  period_end    date,
  body          text not null,             -- 메일 본문 원문
  notes         text,                      -- 작성 방법 메모
  source_file   text,
  created_at    timestamptz not null default now()
);

create table if not exists public.past_report_match (
  report_id       text not null references public.past_report(id) on delete cascade,
  item_ref        text not null,           -- pub_unfit.id / pub_inspection_order.id 등
  customer_label  text not null,           -- 보고서에 적힌 화주 표기(가명)
  primary key (report_id, item_ref, customer_label)
);

alter table public.past_report       enable row level security;
alter table public.past_report_match enable row level security;
revoke all on public.past_report, public.past_report_match from anon, authenticated;
