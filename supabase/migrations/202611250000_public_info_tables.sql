-- weekly_report Supabase: 공개 정보만 (AGENTS.md 5-3). 고객사명·고객사 판단 결과·메일 본문 금지.
-- 쓰기: PM(KHS)만 service_role 키로 (RLS를 우회). 팀원: publishable 키로 읽기만.
-- 그래서 모든 테이블에 RLS를 켜고 SELECT 정책만 둔다. INSERT/UPDATE/DELETE 정책은 만들지 않는다.

create table if not exists public.pub_source_item (
  id            text primary key,                -- {source}:{원문 고유번호} 또는 해시
  source        text not null,                   -- impfood_unfit, mfds_notice, law_api ...
  title         text not null,
  body          text not null default '',
  posted_at     date,
  url           text,
  collected_at  timestamptz not null default now()
);

create table if not exists public.pub_law_change (
  id              text primary key,              -- law:{행정규칙일련번호} 등
  law_name        text not null,
  kind            text check (kind in ('법령','행정규칙')),
  change_type     text,                          -- 제정, 일부개정, 전부개정, 폐지
  number          text,                          -- 고시·공포 번호
  promulgated_at  date,
  effective_at    date,
  articles        text,
  reason_text     text,
  url             text,
  collected_at    timestamptz not null default now()
);

create table if not exists public.pub_unfit (
  id           text primary key,
  unfit_date   date,
  product_ko   text,
  product_en   text,
  food_type    text,
  country      text,
  maker        text,
  violation    text,
  office       text,
  url          text,
  collected_at timestamptz not null default now()
);

create table if not exists public.pub_inspection_order (
  id            text primary key,
  country       text,
  food_type     text,
  items         text,
  period_start  date,
  period_end    date,
  reason        text,
  url           text,
  collected_at  timestamptz not null default now()
);  -- 형식은 정보마루 화면 확인 후 칸 추가(추가만, KHS)

alter table public.pub_source_item      enable row level security;
alter table public.pub_law_change       enable row level security;
alter table public.pub_unfit            enable row level security;
alter table public.pub_inspection_order enable row level security;

create policy "public read" on public.pub_source_item      for select to anon, authenticated using (true);
create policy "public read" on public.pub_law_change       for select to anon, authenticated using (true);
create policy "public read" on public.pub_unfit            for select to anon, authenticated using (true);
create policy "public read" on public.pub_inspection_order for select to anon, authenticated using (true);

create index if not exists pub_unfit_date_idx        on public.pub_unfit (unfit_date);
create index if not exists pub_law_effective_idx     on public.pub_law_change (effective_at);
create index if not exists pub_source_posted_idx     on public.pub_source_item (source, posted_at);
