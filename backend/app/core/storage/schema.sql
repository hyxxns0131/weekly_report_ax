-- 로컬 SQLite 테이블 정의 (C-04, AGENTS.md 5-4). KHS 고정 파일: 바꿀 일이 있으면 PR "변경 요청"에 적는다.
-- 칸은 추가만 한다. 목록·JSON 칸은 TEXT(JSON 문자열)로 둔다. 날짜는 YYYY-MM-DD, 시각은 ISO 8601(KST).

CREATE TABLE IF NOT EXISTS weekly_run (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    reference_date  TEXT NOT NULL,
    period_start    TEXT NOT NULL,
    period_end      TEXT NOT NULL,
    week_label      TEXT NOT NULL,
    created_by      TEXT,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_item (
    id            TEXT PRIMARY KEY,
    run_id        INTEGER NOT NULL REFERENCES weekly_run(id),
    source        TEXT NOT NULL,
    title         TEXT NOT NULL,
    body          TEXT NOT NULL,
    posted_at     TEXT,
    url           TEXT,
    collected_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS selection (
    item_id         TEXT PRIMARY KEY REFERENCES raw_item(id),
    ai_label        TEXT NOT NULL,
    final_label     TEXT,
    ai_category     TEXT NOT NULL,
    final_category  TEXT,
    ai_reason       TEXT NOT NULL DEFAULT '',
    evidence_quote  TEXT NOT NULL DEFAULT '',
    prompt_version  TEXT,
    reviewed_by     TEXT,
    reviewed_at     TEXT
);

CREATE TABLE IF NOT EXISTS extracted_info (
    item_id          TEXT PRIMARY KEY REFERENCES raw_item(id),
    product_name_ko  TEXT,
    product_name_en  TEXT,
    food_type_raw    TEXT,
    food_type_std    TEXT,
    origin_country   TEXT,
    export_country   TEXT,
    maker            TEXT,
    hs_code          TEXT,
    violation        TEXT,
    action           TEXT,
    office           TEXT,
    period_start     TEXT,
    period_end       TEXT,
    edited_fields    TEXT NOT NULL DEFAULT '[]',
    prompt_version   TEXT
);

CREATE TABLE IF NOT EXISTS customer_match (
    item_id        TEXT NOT NULL REFERENCES raw_item(id),
    customer_id    TEXT NOT NULL,
    ai_matched     INTEGER NOT NULL,
    final_matched  INTEGER,
    rule           TEXT NOT NULL,
    confidence     TEXT NOT NULL,
    reason         TEXT NOT NULL,
    PRIMARY KEY (item_id, customer_id)
);

CREATE TABLE IF NOT EXISTS law_change_work (
    id                  TEXT NOT NULL,
    run_id              INTEGER NOT NULL REFERENCES weekly_run(id),
    law_name            TEXT,
    kind                TEXT,
    change_type         TEXT,
    number              TEXT,
    promulgated_at      TEXT,
    effective_at        TEXT,
    articles            TEXT,
    ai_summary          TEXT,
    final_summary       TEXT,
    source_url          TEXT,
    crosscheck          TEXT NOT NULL DEFAULT 'not_checked',
    crosscheck_note     TEXT NOT NULL DEFAULT '',
    related_food_types  TEXT NOT NULL DEFAULT '[]',
    prompt_version      TEXT,
    PRIMARY KEY (id, run_id)
);

CREATE TABLE IF NOT EXISTS weekly_report (
    run_id        INTEGER PRIMARY KEY REFERENCES weekly_run(id),
    body_json     TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'draft',
    updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mail_draft (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id            INTEGER NOT NULL REFERENCES weekly_run(id),
    kind              TEXT NOT NULL,
    customer_id       TEXT,
    subject           TEXT NOT NULL,
    ai_body           TEXT NOT NULL,
    final_body        TEXT,
    warnings          TEXT NOT NULL DEFAULT '[]',
    status            TEXT NOT NULL DEFAULT 'draft',
    sent_at           TEXT,
    gmail_draft_id    TEXT,
    gmail_message_id  TEXT,
    prompt_version    TEXT,
    updated_at        TEXT NOT NULL
);

-- 승인 기록. 발송 API는 이 기록이 없는 초안을 409로 거부한다 (AGENTS.md 0-7)
CREATE TABLE IF NOT EXISTS mail_approval (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id     INTEGER NOT NULL REFERENCES mail_draft(id),
    approved_by  TEXT NOT NULL,
    approved_at  TEXT NOT NULL,
    revoked_at   TEXT
);

CREATE TABLE IF NOT EXISTS eval_result (
    run_id               INTEGER NOT NULL REFERENCES weekly_run(id),
    golden_week          TEXT NOT NULL,
    selection_recall     REAL,
    selection_precision  REAL,
    match_recall         REAL,
    match_precision      REAL,
    review_needed_ratio  REAL,
    missed_items         TEXT NOT NULL DEFAULT '[]',
    extra_items          TEXT NOT NULL DEFAULT '[]',
    wrong_matches        TEXT NOT NULL DEFAULT '[]',
    elapsed_sec          REAL,
    created_at           TEXT NOT NULL,
    PRIMARY KEY (run_id, golden_week)
);

-- 이미 보고한 법령 개정 (기존 도구 weekly_reported.json 역할)
CREATE TABLE IF NOT EXISTS reported_law (
    law_id       TEXT PRIMARY KEY,
    law_name     TEXT,
    effective_at TEXT,
    run_id       INTEGER REFERENCES weekly_run(id),
    reported_at  TEXT NOT NULL
);

-- 메일 초안 수정 이력 (B2-04)
CREATE TABLE IF NOT EXISTS mail_draft_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id    INTEGER NOT NULL REFERENCES mail_draft(id),
    edited_by   TEXT NOT NULL,
    edited_at   TEXT NOT NULL,
    body        TEXT NOT NULL
);

-- 출처별 수집 결과 (B1-01~07, 현황·수집 화면의 "수집 실패 → 수동 업로드" 표시)
CREATE TABLE IF NOT EXISTS collect_log (
    run_id      INTEGER NOT NULL REFERENCES weekly_run(id),
    source      TEXT NOT NULL,
    status      TEXT NOT NULL,  -- ok | failed | manual | off
    count       INTEGER NOT NULL DEFAULT 0,
    message     TEXT NOT NULL DEFAULT '',
    at          TEXT NOT NULL,
    PRIMARY KEY (run_id, source)
);
