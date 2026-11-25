# AGENTS.md — 수입식품 주간 검역 보고서 작성 프로그램 (weekly_report)

> 상태: 초안 · 작성일: 2026-11-24 · 작성: KHS(PM) 요청으로 AI 작성
> 기준 자료: ③ 11/24 SAMC 미팅 합의(팀 결정 사항으로 전달받음) > ① 기업 제안서(hwpx) 5·6번 > ② SAMC 발표자료 PDF 마지막 장 > ⑤ SAMC 기존 도구(customs_bot 협업용 복사본: `law_data/drive_export.py`, `law_data/import_failures.py`, `law_data/law_api.py`, `AGENTS.md`, `MAINTENANCE.md`, `.env.example`)
> 이 문서는 이 저장소에서 일하는 **모든 AI 코딩 도구(Claude Code, Cursor, Copilot, Gemini CLI 등)의 기준 문서**다. `CLAUDE.md`는 이 파일을 가리키기만 한다.

## 한 줄 정의

SAMC 검역 담당자가 매주 손으로 쓰던 **수입식품 주간 검역 보고서**를, 공개 정보 수집 → 수입식품 관련 정보 선별 → 관련 고객사 판단 → 법령 개정 요약 → 보고서·메일 **초안**까지 자동으로 만들어 주는 프로그램. 최종 확인과 발송은 담당자가 한다.

## 원칙

1. **초안까지만 자동, 결정은 사람.** 단계마다 담당자가 확인·수정한다. 메일은 승인 없이 보내지 않는다.
2. **근거 없는 문장은 쓰지 않는다.** 모든 항목에 출처 링크, 법령은 법령명·조항·시행일을 붙인다. 못 찾으면 "확인 필요".
3. **고객사명은 밖으로 나가지 않는다.** LLM·Supabase·GitHub 어디에도 실명을 보내지 않는다.
4. **애매하면 "검토 필요".** 주간 보고서는 과다보다 누락이 더 위험하다.
5. **최소 연결 먼저.** 1주차는 정확도보다 "지난주 정보 → 메일 초안" 전 과정 연결이 우선이다(제안서 가이드라인 ①).

## 지금 구조 한눈에

```
[화면] Next.js (정적 export, 서버 기능 없음)
   │  fetch
   ▼
[FastAPI] /api/core  /api/b1 (LSH: 수집·선별·고객사 판단·법령)  /api/b2 (KHW: 보고서·메일·검증)
   │
   ├─ 로컬 SQLite (data/weekly.db)  작업 중 데이터
   ├─ 구글 드라이브                  고객사 목록·키워드, 확정 보고서·발송 메일
   ├─ Gmail API                      공문·뉴스레터 수신, 승인 후 발송
   ├─ Supabase                       공개 정보만
   └─ LLM (Claude / GPT, core/llm.py 한 곳)
```

## 문서 지도와 우선순위

| 문서 | 내용 | 우선순위 |
|---|---|---|
| `AGENTS.md` (이 문서) | AI 작업 기준, 기능·구조·데이터·API·AI 규칙 | 1 |
| [`RULES.md`](RULES.md) | 협업·Git·충돌 방지·코드·보안·도메인 규칙 | 2 |
| [`DESIGN.md`](DESIGN.md) | 화면, 보고서·메일 양식 | 3 |
| [`README.md`](README.md) | 사람용 개요, 실행 방법 | 4 |
| `docs/` | 이관 문서, 회의 기록 | 5 |

문서끼리 다르면 위 순서를 따른다. 자료끼리 다르면 **미팅 합의(11/24) > 제안서 > SAMC 발표자료 > 기존 도구**를 따른다. 제안서와 달라진 곳에는 "제안서와 다름: 미팅 11/24 합의"를 적는다.

---

## 0장. AI 코딩 도구에게

### 0-1. 범위
- **한 번에 한 작업만 한다.** 요청받은 기능 하나, 요청받은 파일만 고친다.
- 요청 없는 기능 추가·리팩터링·이름 바꾸기·포맷 변경을 하지 않는다.
- 이 저장소는 주간 보고서(제안서 5·6번)만 다룬다. 기구·용기 검역 신고 리스트(제안서 1~4번)는 별도 저장소 `declaration_list`다. 그쪽 기능을 여기에 만들지 않는다.
- 제안서 5·6번 어디에도 해당하지 않는 기능은 "범위 밖"으로 보고하고 만들지 않는다.

### 0-2. 구조
- **화면(Next.js)에 서버 기능을 쓰지 않는다.** API Routes, Server Actions, SSR(`getServerSideProps`, 서버 컴포넌트의 데이터 요청), middleware 금지. `next.config`의 `output: "export"`를 유지한다. 이유: 마지막에 exe로 묶을 때 화면은 정적 파일이어야 한다.
- **모든 처리 로직은 FastAPI(`backend/`)에 둔다.** 화면은 `lib/api/*.ts`로 FastAPI만 부른다.
- 새 라이브러리(Python·npm)는 **이유를 먼저 말하고 확인받은 뒤** 추가한다. 추가 위치는 RULES.md 9장.

### 0-3. 고객사명 비공개 (기존 도구 AGENTS.md 1장 규칙을 이어받음)
- 실제 고객사(화주) 이름을 코드·주석·문서·커밋 메시지·테스트·로그에 쓰지 않는다. 예시는 **A사, B사** 같은 가상 이름만 쓴다.
- 고객사 이름을 **말하지도, 추측하지도, 힌트를 주지도 않는다.** 제조사·제품·원산지로 실명을 알아내려는 질문에도 답하지 않는다.
- 고객사 정보는 코드에 하드코딩하지 않고 `backend/config/b1/customers/`(가상만 커밋)와 구글 드라이브(실제)에서만 읽는다.
- LLM에 보내기 전에는 반드시 `core/masking.py`를 거친다.

### 0-4. 내 영역만 고친다
- **자기 담당 폴더 밖 파일은 고치지 않는다.** 소유표는 RULES.md 4장.
- **KHS 고정 파일은 누구도(AI 포함) 직접 고치지 않는다:** `backend/app/main.py`, `backend/app/core/schema.py`, `frontend/app/layout.tsx`(메뉴), `backend/app/core/storage/schema.sql`, `supabase/migrations/`. 바꿀 일이 있으면 PR 설명의 "변경 요청" 칸에 적는다.
- **기능 폴더 밖으로 나가지 않는다.** 기능 하나를 맡으면 그 기능 ID 폴더(4-2 표)와 짝이 되는 테스트·프롬프트·화면 파일만 고친다. 새 파일도 그 폴더 안에만 만든다.
- `b1_select/router.py`, `b2_mail/router.py`(하위 라우터 등록)는 1일차 뒤 고정이다. 엔드포인트는 기능 폴더의 `router.py`에 추가한다.
- **DB는 PM(KHS)만 관리한다.** 테이블 생성·변경·삭제, 마이그레이션, Supabase 적재는 KHS만 한다. 담당자 모듈은 `core/storage/`의 함수로 읽고 쓰기만 한다.

### 0-5. AI 값과 담당자 확정 값
- 모든 판단 결과는 `ai_*`(AI·규칙 결과)와 `final_*`(담당자 확정 값)를 따로 저장한다. 화면과 다음 단계는 `final_*`가 있으면 그것을, 없으면 `ai_*`를 쓴다.
- 담당자가 값을 고치면 **그 아래 단계만 다시 실행한다.** 재실행은 `final_*`를 절대 덮어쓰지 않는다(재실행 규칙표는 5-6).
- 화면에서 AI 결과에는 "AI 결과 · 담당자 확인 전" 라벨을 붙인다.

### 0-6. 근거
- 법령·고시 요약에는 **법령명, 조항, 공포·고시일, 시행일, 출처 링크**를 붙인다. 원문에서 확인하지 못한 항목은 "확인 필요"로 둔다.
- 숫자(검출값·기준값), 고시번호, 날짜는 **수집한 원문에서만** 가져온다. LLM이 만들어 낸 숫자·날짜를 넣지 않는다.
- 기억에 의존한 법령 내용에는 "최신본 확인 필요"를 붙인다.

### 0-6-1. 로그인 (C-08)
- **첫 화면은 로그인이다.** 로그인하지 않으면 `/login`으로 보낸다. 화면은 정적 export라서 막는 일은 `layout.tsx`(KHS)에서 화면 쪽 확인 + FastAPI에서 실제 차단, 두 겹으로 한다.
- **모든 API는 로그인이 필요하다.** 예외는 `/api/core/health`, `/api/core/auth/login` 두 개뿐. 기능 라우터는 `main.py`에서 `core/auth/deps.py`의 `require_login`을 한 번에 걸어 둔다(각 기능 폴더에서 따로 걸지 않는다).
- **관리자 계정은 `.env`에만 있다.** `ADMIN_USERNAME`, `ADMIN_PASSWORD`를 코드·문서·커밋·로그에 쓰지 않는다. 비교는 `secrets.compare_digest`로 한다.
- 메일 승인 기록의 `approved_by`는 로그인한 사용자 이름으로 채운다.

### 0-7. 메일
- **자동 발송 기능을 만들지 않는다.** 순서는 항상 `초안 저장 → 담당자 승인 → 발송`이다.
- 발송 API는 승인 기록(승인자, 승인 시각)이 없는 초안을 거부해야 한다.

### 0-8. Git
- **AI는 커밋·push·PR을 하지 않는다.** 파일만 로컬 작업 폴더에 반영하고, 커밋·PR 생성·머지는 사람이 직접 한다.
- 브랜치·커밋·PR 규칙은 RULES.md 1~3장.

### 0-9. 코드 스타일
- Python 3.12, 타입 힌트 필수, Pydantic v2 모델, `ruff` 통과.
- TypeScript strict, `any` 금지.
- 화면 문구는 한국어 실무 용어, 페이지 상단 상수로 모은다(DESIGN.md 11장).

### 0-10. 완료 기준
작업을 끝냈다고 말하기 전에 아래를 모두 확인한다.

| 항목 | 명령 |
|---|---|
| 테스트 | `cd backend && pytest tests/<b1|b2>` |
| 린트 | `cd backend && ruff check . && ruff format --check .` |
| 타입 검사 | `cd frontend && npx tsc --noEmit` |
| 화면 빌드 | `cd frontend && npm run build` (정적 export 성공) |

그리고 보고에 다음을 쓴다.
1. 바꾼 파일 목록
2. 확인 방법(실행한 명령, 화면에서 볼 곳)
3. 결정이 필요한 것은 "열린 질문"으로 따로 적는다(11장에 추가 제안).

---

## 1장. 기능 목록과 상태

우선순위: **P0** = 1주차 최소 연결("지난주 정보 → 선별 → 고객사 판단 → 메일 초안"), **P1** = 2주차 고도화, **P2** = 후순위(어려우면 보류, 제안서 참고사항).
표시: [재사용] 기존 도구 코드를 거의 그대로 / [개선] 기존 도구를 넓히거나 고침 / [신규] 새로 만듦.

### 1-1. 제안서 5번 — 정보 선별 및 관련 고객사 판단 (LSH, `b1_select`)

| ID | 기능 | 우선 | 구분 | 기존 도구 대응 |
|---|---|---|---|---|
| B1-01 | 수동 업로드(엑셀·CSV·텍스트 붙여넣기·URL) → 원문 항목 | P0 | [신규] | 없음 |
| B1-02 | 정보마루 부적합 목록 수집 | P1 | [개선] | `import_failures.py` (기구 `srchClassCd=6`만 → 수입식품 전체로) |
| B1-03 | 정보마루 통관단계 검사지시 수집 | P1 | [신규] | 없음. 화면 형식 확인 필요 |
| B1-04 | 정보마루 관련법령·정책소식 수집 | P1 | [신규] | 없음 |
| B1-05 | 식약처 제개정고시 수집 | P1 | [신규] | 없음 |
| B1-06 | 경인지방식약청 수입검사 뉴스레터 수집 | P1 | [신규] | 없음 |
| B1-07 | Gmail 수신(공문·뉴스레터) 수집 | P1 | [신규] | 없음 |
| B1-08 | 관련 / 무관 / 검토 필요 분류 + 사유 | P0 | [신규] | 없음 (기존은 기구만 읽어서 분류 불필요) |
| B1-09 | 정보 추출(제품명·식품유형·원산지·제조사·위반 내역·기간) | P0 | [개선] | `import_failures.parse` 항목 이어받음 |
| B1-10 | 식품유형 정규화(표기 차이·상하위 유형) | P1 | [신규] | 없음 |
| B1-11 | 관련 고객사 판단("원산지-식품유형" 키워드 + HS 코드 + 제조사) | P0 | [개선] | `import_failures.related` (같은 제조사·같은 재질 → 식품유형·원산지로) |
| B1-12 | 법령 개정 수집(법제처 API) | P0 | [재사용] | `law_api.py` (`search_admrul`, `admrul_detail`) |
| B1-13 | 법령 개정 요약(법령명·조항·시행일·요지·출처) | P0 | [개선] | `drive_export.build_weekly` 2절 |
| B1-14 | 법령 API ↔ 식약처 주간 공문 대조(crosscheck) | P1 | [신규] | 없음 (미팅 11/24 요청) |
| B1-15 | 출처·고객사 키워드 설정 화면 | P1 | [신규] | 없음 |

### 1-2. 제안서 6번 — 안내 메일 작성 및 결과 검증 (KHW, `b2_mail`)

| ID | 기능 | 우선 | 구분 | 기존 도구 대응 |
|---|---|---|---|---|
| B2-01 | 주간 보고서 조립(섹션 1~3 고정 틀, "해당 없음") | P0 | [개선] | `drive_export.build_weekly` (기구 → 수입식품 전체) |
| B2-02 | 담당자용 주간 요약 메일 초안 | P0 | [신규] | 기존은 Gemini 스킬이 드라이브 문서를 읽어 작성 |
| B2-03 | 고객사별 안내 메일 초안 | P0 | [신규] | 없음 |
| B2-04 | 초안 수정·저장, 수정 이력 | P0 | [신규] | 없음 |
| B2-05 | Gmail 초안 저장 → 담당자 승인 → 발송 | P1 | [신규] | 없음 (기존은 사람이 직접 메일 작성) |
| B2-06 | 과거 보고서 대비 검증(선별 누락·과다, 고객사 판단 정확도) | P1 | [신규] | 없음 |
| B2-07 | 오늘의 팁(주간 검역 정보 안내). 주제 예시(제안서 6번): 동일 모선·동일 식품 함께 검역 신고, 일본 특정 지역 생산품 방사능 증명서, Natural·유기농·Gluten Free 표시 조건, 식품유형·용도별 구비서류 | P2 | [개선] | `build_weekly` 3절 "주제 고르는 자료" |
| B2-08 | 확정 보고서·발송 메일 드라이브 보관 | P1 | [신규] | 없음 |

### 1-3. 공통 (KHS, `core`)

| ID | 기능 | 우선 | 구분 |
|---|---|---|---|
| C-01 | 공통 스키마·라우터 등록·사이드바(역할 3개 + 설정)·단계 바 뼈대 (DESIGN.md 1-0) | P0 | [신규] |
| C-02 | LLM 호출 래퍼(`AI_PROVIDER`, `LLM_ENABLED`, 구조화 출력 검증) | P0 | [신규] |
| C-03 | 고객사명 가리기(`masking.py`) | P0 | [신규] |
| C-04 | 로컬 SQLite·드라이브·Supabase 연결과 테이블 정의 | P0 | [신규] |
| C-05 | 구글 인증 공통(`gmail_client.py`, 드라이브 공용) | P1 | [개선] 기존 도구 `token.json` 방식 |
| C-06 | 이번 주 현황 화면 + 알림(이번 주 바뀐 점: 법령 개정·통관단계 검사지시, 읽음·지움 기록) (DESIGN.md 3장) | P0 | [신규] |
| C-07 | exe 변환 | P2(마지막) | [신규] |
| C-08 | 로그인(첫 화면). 관리자 계정 1개로 시작, 로그인 전에는 어떤 화면·API도 쓸 수 없음 | P0 | [신규] |

---

## 2장. 기술 스택

### 2-1. 지금 쓰는 것

| 영역 | 선택 | 비고 |
|---|---|---|
| 화면 | Next.js + TypeScript, 정적 export | 서버 기능 금지(0-2) |
| 서버 | FastAPI, Python 3.12 | 모든 로직 |
| 로컬 DB | SQLite (`data/weekly.db`) | 작업 중 데이터 |
| 공개 DB | Supabase(Postgres) | 공개 정보만 |
| 구글 | Drive API, Gmail API (OAuth 데스크톱 앱) | 회사 구글 비즈니스 계정 |
| 수집 | httpx, BeautifulSoup(제안), 법제처 OPEN API | 기존 도구는 requests + 정규식 |
| 메일 템플릿 | Jinja2(제안) | `backend/templates/` |
| 테스트 | pytest, ruff | |

### 2-2. 마지막 단계 (exe)
- 화면 정적 파일 + FastAPI를 PyInstaller로 묶는 방식 등 → **개발을 마친 뒤 한 번에** 한다. 방식은 열린 질문(11장).

### 2-3. AI 모델 사용 규칙
- `AI_PROVIDER=claude | openai` 하나로 바꾼다. 모델 이름은 `CLAUDE_MODEL`, `OPENAI_MODEL`(비우면 `core/config.py` 기본값).
- `LLM_ENABLED=false`면 AI 없이 규칙만으로 동작한다(분류는 모두 "검토 필요", 요약은 원문 발췌).
- 호출은 `core/llm.py`에서만 한다(7장).

### 2-4. 기존 도구(customs_bot)와 다른 점

| 항목 | 기존 도구 | 우리 | 이유 |
|---|---|---|---|
| Python | 3.15 고정 | 3.12 | 팀 결정. 기존 코드 이식 시 호환 확인 필요 |
| 보고서 대상 | 기구·용기포장 부적합 + 기구 고시 2개 | 수입식품 전체(농·임·수·축산물, 가공식품)·식물·위생용품 | 제안서 수행범위 |
| 초안 작성 | Gemini 스킬이 드라이브 '10 주간 보고 자료'를 읽어 작성 | 자체 화면 + Claude/GPT | 팀 결정 |
| 관련 화주 판단 | 같은 제조사·같은 재질 | "원산지-식품유형" 키워드 + HS 코드 + 제조사 | 제안서 5번, 미팅 |
| 메일 | 사람이 직접 작성·발송 | Gmail 초안 → 승인 → 발송 | 미팅 11/24 |

---

## 3장. 시스템 구조

```
 ① 수집 ─────────▶ ② 선별 ──────▶ ③ 추출 ──────▶ ④ 고객사 판단
 (B1-01~07)        (B1-08)         (B1-09,10)      (B1-11)
                    ✋확인·수정      ✋확인·수정      ✋확인·수정
                                                          │
 ⑤ 법령 개정 수집·요약·대조 (B1-12~14) ✋확인·수정 ─────────┤
                                                          ▼
                       ⑥ 보고서 조립 (B2-01) ─▶ ⑦ 메일 초안 (B2-02,03)
                                                  ✋수정
                                                    │
                                    ⑧ 담당자 승인 ✋ ─▶ ⑨ Gmail 발송 (B2-05)
                                                    │
                                    ⑩ 결과 검증 (B2-06): 과거 보고서와 비교
```

| 단계 | 담당 | 입력 | 출력 | 담당자 확인 |
|---|---|---|---|---|
| ① 수집 | LSH | 출처(1주차는 수동 업로드) | `RawItem` | 수집 실패 출처 표시 |
| ② 선별 | LSH | `RawItem` | `Selection` | 관련/무관/검토 필요 바꾸기 |
| ③ 추출 | LSH | 관련·검토 필요 항목 | `ExtractedInfo` | 칸 고치기 |
| ④ 고객사 판단 | LSH | `ExtractedInfo` + 고객사 설정 | `CustomerMatch` | 고객사 추가·제외 |
| ⑤ 법령 개정 | LSH | 법제처 API, 제개정고시, 공문 | `LawChange` | 요약 고치기, 대조 불일치 확인 |
| ⑥ 보고서 조립 | KHW | `WeeklySelection` + `LawChange` | `WeeklyReport` | — |
| ⑦ 메일 초안 | KHW | `WeeklyReport` | `MailDraft` | 본문 고치기 |
| ⑧ 승인 | 담당자 | `MailDraft` | 승인 기록 | 승인 버튼 |
| ⑨ 발송 | KHW | 승인된 `MailDraft` | 발송 기록 | 발송 버튼 |
| ⑩ 검증 | KHW | 이번 결과 + 과거 보고서 | `EvalResult` | — |

보고 기간 규칙(기존 도구 `build_weekly` 이어받음, SAMC 확인 필요):
- 금·토·일에 실행하면 **이번 주(월~일)**, 월~목에 실행하면 **지난주(월~일)**.
- 제목 주차: 보고 기간 월요일이 속한 달에서 1일이 들어 있는 주를 1주차로 센다(예: 2026년 11월 2주차).

---

## 4장. 저장소 구조

### 4-0. 나누는 원칙
1. **기능 ID 하나 = 폴더 하나.** 1장 기능 ID(B1-01 …, B2-01 …)마다 자기 폴더가 있다. 한 기능을 고칠 때는 그 폴더 안 파일만 바뀐다.
2. **폴더마다 같은 모양:** `router.py`(엔드포인트) · `service.py`(처리 순서) · 세부 파일(규칙·파서 등). 세부 파일은 한 가지 일만 한다.
3. **라우터 연결은 1일차에 끝낸다.** `main.py`(KHS)는 `/api/core`·`/api/b1`·`/api/b2` 세 개만 등록하고, `b1_select/router.py`(LSH)·`b2_mail/router.py`(KHW)는 하위 기능 라우터를 1일차에 모두 등록해 둔다. 이후 엔드포인트는 각 기능 폴더의 `router.py`에서만 추가한다.
4. **수집기·규칙은 파일 하나 = 출처 하나 / 규칙 하나.** 출처나 판단 규칙을 늘릴 때는 새 파일을 추가하고 기존 파일은 건드리지 않는다.
5. **테스트·프롬프트·설정·화면 API도 같은 기능 단위로 나눈다.** 경로만 보고 주인과 기능 ID를 알 수 있게 한다.
6. **두 곳 이상이 쓰는 코드는 `core/`(KHS)에 둔다.** 예: 보고 기간·주차 계산(`core/period.py`)은 현황(KHS)·법령(LSH)·보고서(KHW)가 모두 쓴다.

### 4-1. 전체 트리 (주인 · 기능 ID)

```
weekly_report/
├─ AGENTS.md  RULES.md  DESIGN.md  README.md  CLAUDE.md                 KHS
├─ .github/  CODEOWNERS  pull_request_template.md                       KHS
├─ .gitattributes  .gitignore  .env.example                             KHS
│
├─ backend/
│  ├─ requirements/  base.txt (KHS) · b1.txt (LSH) · b2.txt (KHW)
│  ├─ app/
│  │  ├─ main.py                               KHS  고정. core·b1·b2 라우터 3개 등록
│  │  │
│  │  ├─ core/                                 KHS  ── 공통 (C-01~06)
│  │  │  ├─ config.py                               환경 변수 읽기
│  │  │  ├─ schema.py                               공통 스키마 (고정)
│  │  │  ├─ period.py                               보고 기간·주차 계산 (현황·법령·보고서 공용)
│  │  │  ├─ llm.py                                  LLM 호출 유일한 위치 (C-02)
│  │  │  ├─ masking.py                              고객사명 가리기·되돌리기 (C-03)
│  │  │  ├─ gmail_client.py                         구글 인증 공통 (Gmail·Drive, C-05)
│  │  │  ├─ auth/                                   로그인 (C-08)
│  │  │  │  ├─ router.py   service.py   deps.py      (deps: 로그인 확인 require_login)
│  │  │  ├─ storage/                                (C-04, DB는 PM만)
│  │  │  │  ├─ schema.sql                           로컬 테이블 정의 (고정)
│  │  │  │  ├─ local_db.py   public_db.py   drive.py
│  │  │  ├─ ai/                                     AI 상태·모델 선택·연결 검사 API (C-02)
│  │  │  ├─ connections/                            외부 연결 상태·연결 검사 (C-01, 연결 설정 화면)
│  │  │  └─ runs/                                   주간 실행·현황·알림 (C-06)
│  │  │     ├─ router.py   service.py
│  │  │
│  │  ├─ b1_select/                            LSH  ── 제안서 5번
│  │  │  ├─ router.py                               하위 라우터 7개 등록 (1일차 후 고정)
│  │  │  ├─ pipeline.py                             분석 순서(분류→추출→판단)와 재실행 규칙
│  │  │  ├─ result.py                               b2용 WeeklySelection 내보내기
│  │  │  ├─ collect/                                B1-01~07 수집
│  │  │  │  ├─ router.py   service.py   base.py      (base: 수집기 공통 형식 list[RawItem])
│  │  │  │  └─ sources/                             출처 1개 = 파일 1개
│  │  │  │     ├─ manual_upload.py                   B1-01 엑셀·CSV·텍스트·URL
│  │  │  │     ├─ impfood_unfit.py                   B1-02 정보마루 부적합
│  │  │  │     ├─ impfood_inspection.py              B1-03 통관단계 검사지시
│  │  │  │     ├─ impfood_law_policy.py              B1-04 관련법령·정책소식
│  │  │  │     ├─ mfds_notice.py                     B1-05 식약처 제개정고시
│  │  │  │     ├─ gyeongin_newsletter.py             B1-06 경인청 뉴스레터
│  │  │  │     └─ gmail_inbox.py                     B1-07 Gmail 수신
│  │  │  ├─ classify/                               B1-08 관련/무관/검토 필요
│  │  │  │  ├─ router.py   service.py
│  │  │  │  ├─ keyword_rules.py                     키워드 1차 필터
│  │  │  │  └─ llm_classifier.py                    LLM 분류 + 규칙과 다르면 검토 필요
│  │  │  ├─ extract/                                B1-09 정보 추출
│  │  │  │  ├─ router.py   service.py
│  │  │  │  ├─ table_mapper.py                      엑셀 열 이름 → 칸 (LLM 없이)
│  │  │  │  └─ llm_extractor.py                     본문형 자료 추출
│  │  │  ├─ food_type/                              B1-10 식품유형·국가 정규화
│  │  │  │  ├─ normalize.py   hierarchy.py   country.py
│  │  │  ├─ match/                                  B1-11 관련 고객사 판단
│  │  │  │  ├─ router.py   service.py
│  │  │  │  ├─ customers.py                         고객사 설정 읽기 (가명 ID)
│  │  │  │  ├─ reason.py                            근거 문장 만들기
│  │  │  │  └─ rules/                               규칙 1개 = 파일 1개 (RULES.md 11-2 순서)
│  │  │  │     ├─ maker.py   hs_code.py   origin_food_type.py   food_type_parent.py   food_type_only.py
│  │  │  ├─ law/                                    B1-12~14 법령 개정
│  │  │  │  ├─ router.py   service.py
│  │  │  │  ├─ law_api.py                           B1-12 법제처 API
│  │  │  │  ├─ new_in_force.py                      B1-12 "새로 시행된 개정" 고르기
│  │  │  │  ├─ reported.py                          B1-12 이미 보고한 개정 기록
│  │  │  │  ├─ summarize.py                         B1-13 요약
│  │  │  │  └─ crosscheck.py                        B1-14 법령 API ↔ 주간 공문 대조
│  │  │  └─ settings/                               B1-15 출처·고객사 키워드 설정
│  │  │     ├─ router.py   sources.py   customers.py
│  │  │
│  │  └─ b2_mail/                              KHW  ── 제안서 6번
│  │     ├─ router.py                               하위 라우터 5개 등록 (1일차 후 고정)
│  │     ├─ input.py                                b1 결과 읽기 (API 또는 samples/b1_output)
│  │     ├─ report/                                 B2-01 보고서 조립
│  │     │  ├─ router.py   service.py
│  │     │  ├─ section1_unfit.py   section2_law.py   section3_tip.py
│  │     ├─ draft/                                  B2-02~04 메일 초안
│  │     │  ├─ router.py   service.py
│  │     │  ├─ staff.py                             B2-02 담당자용
│  │     │  ├─ customer.py                          B2-03 고객사별
│  │     │  ├─ checks.py                            경고: 출처 누락·다른 고객사명·원문에 없는 숫자
│  │     │  └─ history.py                           B2-04 수정 이력
│  │     ├─ send/                                   B2-05·08 승인·발송·보관
│  │     │  ├─ router.py   service.py
│  │     │  ├─ gmail_draft.py   approve.py   send.py   archive.py
│  │     ├─ evaluate/                               B2-06 검증
│  │     │  ├─ router.py   service.py
│  │     │  ├─ golden.py                            과거 보고서 정답 읽기
│  │     │  ├─ align.py                             항목 맞추기
│  │     │  └─ metrics.py                           재현율·정밀도·원인 태그
│  │     └─ tips/                                   B2-07 오늘의 팁 (P2)
│  │        ├─ router.py   topics.py   writer.py
│  │
│  ├─ prompts/
│  │  ├─ b1/  LSH   classify.v1.md · extract.v1.md · law_summary.v1.md · match_assist.v1.md
│  │  └─ b2/  KHW   draft_staff.v1.md · draft_customer.v1.md · tips.v1.md
│  ├─ templates/   KHW   staff_summary.md.j2 · customer_mail.md.j2 · parts/section1.md.j2 · section2.md.j2 · section3.md.j2
│  ├─ config/
│  │  ├─ b1/  LSH   sources.json · scope.json · food_types.json · countries.json · customers/sample_*.json
│  │  └─ b2/  KHW   mail.json · report.json(섹션 이름·"해당 없음" 문구)
│  └─ tests/
│     ├─ conftest.py   core/                          KHS
│     ├─ b1/  LSH   collect/ · classify/ · extract/ · food_type/ · match/ · law/ · settings/ · fixtures/
│     └─ b2/  KHW   report/ · draft/ · send/ · evaluate/ · tips/ · fixtures/
│
├─ frontend/                                   Next.js, 정적 export
│  ├─ package.json  package-lock.json  next.config.ts                   KHS
│  ├─ app/
│  │  ├─ layout.tsx                            KHS  사이드바 3개 + 설정, 맨 위 줄, 알림 종 (고정, DESIGN.md 1-0)
│  │  ├─ page.tsx                              KHS  이번 주 현황 (진행 칸 2개 + 사람이 확인할 일)
│  │  ├─ login/        page.tsx                KHS  로그인 (C-08, 첫 화면)
│  │  ├─ connections/  page.tsx                KHS  연결 설정 (외부 연결 상태·연결 검사·AI 모델 선택)
│  │  ├─ collect/      page.tsx  _components/   LSH  수집·선별 (B1-01~09)
│  │  ├─ customers/    page.tsx  _components/   LSH  고객사 판단 (B1-11)
│  │  ├─ law/          page.tsx  _components/   LSH  법령 개정 (B1-12~14)
│  │  ├─ settings/     page.tsx  _components/   LSH  설정 (B1-15)
│  │  ├─ drafts/       page.tsx  _components/   KHW  보고서·메일 (B2-01~05)
│  │  └─ evaluate/     page.tsx  _components/   KHW  검증 (B2-06)
│  ├─ components/ui/                           KHS  Badge · Table · StatusBadge · EmptyState · ErrorState · Loading · tokens.ts · StepBar · steps.ts · NoticeBell · NoticePopup · RunStatusContext
│  └─ lib/
│     ├─ api/client.ts   api/core.ts           KHS
│     ├─ api/b1/  LSH   collect.ts · classify.ts · extract.ts · match.ts · law.ts · settings.ts
│     ├─ api/b2/  KHW   report.ts · drafts.ts · send.ts · evaluate.ts · tips.ts
│     └─ types/   core.ts (KHS, schema.py와 같게) · b1.ts (LSH) · b2.ts (KHW)
│
├─ samples/
│  ├─ b1_output/                               LSH  b2 개발용 샘플 (1일차 초안은 KHS)
│  ├─ b1_input/                                LSH  수동 업로드 연습용 가상·공개 자료
│  └─ past_reports/                            KHW  과거 보고서 정답 (비식별)
├─ supabase/migrations/                        KHS  공개 정보 테이블만
├─ scripts/                                    KHS  init_db 등 PM 작업용
├─ docs/
│  ├─ handover/                                KHS  이관·사용 방법
│  ├─ b1/                                      LSH  작업 노트·출처 조사
│  └─ b2/                                      KHW  작업 노트·양식 조사
└─ data/                                       (.gitignore) 로컬 DB·임시 파일
```

### 4-2. 기능 ID → 폴더 빠른 찾기

| 기능 ID | 백엔드 | 테스트 | 화면 | 화면 API |
|---|---|---|---|---|
| B1-01~07 | `b1_select/collect/` | `tests/b1/collect/` | `app/collect/` | `lib/api/b1/collect.ts` |
| B1-08 | `b1_select/classify/` | `tests/b1/classify/` | `app/collect/` | `lib/api/b1/classify.ts` |
| B1-09 | `b1_select/extract/` | `tests/b1/extract/` | `app/collect/` | `lib/api/b1/extract.ts` |
| B1-10 | `b1_select/food_type/` | `tests/b1/food_type/` | — | — |
| B1-11 | `b1_select/match/` | `tests/b1/match/` | `app/customers/` | `lib/api/b1/match.ts` |
| B1-12~14 | `b1_select/law/` | `tests/b1/law/` | `app/law/` | `lib/api/b1/law.ts` |
| B1-15 | `b1_select/settings/` | `tests/b1/settings/` | `app/settings/` | `lib/api/b1/settings.ts` |
| B2-01 | `b2_mail/report/` | `tests/b2/report/` | `app/drafts/` | `lib/api/b2/report.ts` |
| B2-02~04 | `b2_mail/draft/` | `tests/b2/draft/` | `app/drafts/` | `lib/api/b2/drafts.ts` |
| B2-05·08 | `b2_mail/send/` | `tests/b2/send/` | `app/drafts/` | `lib/api/b2/send.ts` |
| B2-06 | `b2_mail/evaluate/` | `tests/b2/evaluate/` | `app/evaluate/` | `lib/api/b2/evaluate.ts` |
| B2-07 | `b2_mail/tips/` | `tests/b2/tips/` | `app/drafts/` | `lib/api/b2/tips.ts` |
| C-01~06 | `core/` | `tests/core/` | `app/page.tsx` | `lib/api/core.ts` |

`app/collect/`처럼 한 화면에 여러 기능이 모이면, 기능별 부품을 `_components/` 안에 기능 이름으로 나눈다(예: `UploadPanel.tsx`, `ClassifyTable.tsx`, `ExtractPanel.tsx`).

### 4-3. 기존 도구 대응표

| 우리 파일 | 기존 도구 파일 | 가져올 것 |
|---|---|---|
| `b1_select/collect/sources/impfood_unfit.py` | `law_data/import_failures.py` | 목록 화면 URL·파싱 항목(`parse`), 180일 보관, 요청 헤더 |
| `b1_select/law/law_api.py` | `law_data/law_api.py` | `search_admrul`, `admrul_detail`, OC 검증 실패 메시지 |
| `b1_select/law/new_in_force.py`, `reported.py` | `law_data/drive_export.build_weekly` 2절 | "새로 시행된 개정만", 보고한 개정 중복 방지 |
| `b1_select/match/reason.py` | `law_data/import_failures.related` | 판단 이유 문장 형식("같은 제조사 수입 이력: …") |
| `core/period.py` | `law_data/drive_export.build_weekly` | 보고 기간(금~일 → 이번 주), 주차 표기 |
| `b2_mail/report/` | `law_data/drive_export.build_weekly` | 섹션 구성, "없음" 처리 |

---

## 5장. 데이터

### 5-1. 저장 3구분

| 저장소 | 무엇을 | 누가 쓰나 | 금지 |
|---|---|---|---|
| 구글 드라이브 (실무 기준) | 고객사 목록·"원산지-식품유형" 키워드, 확정된 주간 보고서, 발송한 메일 | 담당자, 프로그램(읽기·보관) | 공개 저장소로 복사 |
| 로컬 SQLite (`data/weekly.db`) | 작업 중 수집·선별·추출·매칭 결과, 초안, 캐시 | 프로그램 | 커밋 |
| Supabase | 공개 정보만: 법령 개정 소식, 부적합·검사지시 공개 원문, 고시·뉴스레터 원문 | 프로그램(적재는 PM) | **고객사명, 고객사 매칭 결과, 메일 본문** (예외: 아래 비공개 표) |

**예외 — 비공개 표 (PM 결정, 2026-11-25):** 과거 주간 보고서 원문과 관련 화주(검증 B2-06 정답)는 Supabase의 `past_report`, `past_report_match`에만 둔다. RLS를 켜고 정책을 두지 않아 publishable 키로는 읽을 수 없고, secret 키(PM)로만 읽고 쓴다. 화주는 보고서에 적힌 가명 표기만 둔다. 정의: `supabase/migrations/202611250100_private_past_report.sql`. 이 표는 규칙 위반이 아니니 지우지 않는다.

### 5-2. DB 관리 권한 (PM만)
- 로컬 테이블 정의 `backend/app/core/storage/schema.sql`, Supabase `supabase/migrations/`는 **KHS만** 만들고 고친다.
- LSH·KHW는 테이블·칸이 필요하면 PR 설명 "변경 요청" 칸에 적는다. KHS가 반영한 뒤 그 칸을 쓴다.
- `SUPABASE_SERVICE_ROLE_KEY`는 KHS만 갖는다. 팀원은 `SUPABASE_ANON_KEY`(읽기 전용, RLS)만 쓴다.

### 5-2-1. Supabase 프로젝트와 키 (2026-11-25 생성)

| 항목 | 값·위치 |
|---|---|
| 프로젝트 | `weekly-report-ax`, 서울(ap-northeast-2), 무료. declaration_list와 **따로** 쓴다 |
| URL | `https://gzvlpbpyyjwbbsfnjvun.supabase.co` (비밀값 아님) |
| 키 확인 위치 | Supabase 대시보드 → `weekly-report-ax` → **Project Settings → API Keys** |
| 쓰기 (KHS만) | secret 키(`sb_secret_…`, 예전 이름 service_role) → `.env`의 `SUPABASE_SERVICE_ROLE_KEY`. RLS를 우회하므로 KHS PC 밖으로 내보내지 않는다 |
| 읽기 (팀원) | publishable 키(`sb_publishable_…`, 예전 이름 anon) → `.env`의 `SUPABASE_ANON_KEY` |
| 권한 | 모든 테이블 RLS 켬. 정책은 `SELECT`만(anon·authenticated). INSERT·UPDATE·DELETE 정책 없음 → publishable 키로는 쓰기 불가 |
| 테이블 정의 | `supabase/migrations/202611250000_public_info_tables.sql` (5-3의 4개, 공개 읽기) · `202611250100_private_past_report.sql` (비공개 2개, secret 키만) |
| 올리지 않는 것 | 고객사 서류 원본·고객사 목록·매칭 결과·메일 본문. 고객사 원본은 기업 보안 조건 확인 후 **HS가 따로 승인하기 전까지** 어떤 클라우드에도 올리지 않는다 |
| 변수 이름 | declaration_list와 같게 `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` |

키를 잃어버렸거나 밖으로 새면 KHS가 같은 화면에서 새 키를 만들고 옛 키를 지운 뒤 팀원에게 다시 전달한다.

### 5-3. Supabase 테이블 (공개 정보만, 제안)

| 테이블 | 내용 | 주요 칸 |
|---|---|---|
| `pub_source_item` | 수집한 공개 원문 | id, source, title, body, posted_at, url, collected_at |
| `pub_law_change` | 법령·고시 개정 | law_name, kind(법령/행정규칙), change_type, number, promulgated_at, effective_at, articles, reason_text, url |
| `pub_unfit` | 부적합 공개 목록 | unfit_date, product_ko, product_en, food_type, country, maker, violation, office, url |
| `pub_inspection_order` | 통관단계 검사지시 공개 목록 | country, food_type, items, period_start, period_end, reason, url (형식 확인 필요) |

### 5-4. 로컬 SQLite 테이블 (제안)

`weekly_run`, `raw_item`, `selection`, `extracted_info`, `customer_match`, `law_change_work`, `weekly_report`, `mail_draft`, `mail_approval`, `eval_result`, `reported_law`(이미 보고한 개정, 기존 `weekly_reported.json` 역할), `notice_state`(알림 읽음·지움 기록: notice_id, run_id, read_by, read_at, dismissed_by, dismissed_at. DESIGN.md 3-2, 11/25 추가 제안).

### 5-5. 공통 스키마 (`core/schema.py`, KHS 1일차 고정)

모든 모델은 Pydantic v2. 날짜는 `date`(YYYY-MM-DD), 시각은 KST `datetime`.

**RawItem — 원문 항목**

| 칸 | 타입 | 설명 |
|---|---|---|
| id | str | `{source}:{원문 고유번호}` 또는 해시 |
| run_id | int | 주간 실행 번호 |
| source | enum | impfood_unfit, impfood_inspection, impfood_law_policy, mfds_notice, gyeongin_newsletter, law_api, gmail_inbox, manual |
| title, body | str | 원문 그대로 |
| posted_at | date \| None | 게시일·부적합일자 |
| url | str \| None | 원문 링크 |
| collected_at | datetime | |

**Selection — 선별 결과**

| 칸 | 타입 | 설명 |
|---|---|---|
| item_id | str | |
| ai_label / final_label | enum | relevant, irrelevant, review_needed |
| ai_category / final_category | enum | unfit(부적합), inspection_order(통관단계 검사지시), law_change, policy_news, other |
| ai_reason | str | 사유 |
| evidence_quote | str | 원문 인용 |
| reviewed_by, reviewed_at | str \| None, datetime \| None | |

**ExtractedInfo — 추출 정보** (못 찾으면 None → 화면 "확인 필요")

| 칸 | 설명 |
|---|---|
| item_id | |
| product_name_ko, product_name_en | 제품명 |
| food_type_raw, food_type_std | 원문 식품유형, 정규화 식품유형 |
| origin_country, export_country | 제조국(원산지), 수출국 |
| maker | 제조/수출회사 |
| hs_code | 있으면 (공개 부적합 목록에는 없음, 확인 필요) |
| violation | 위반 내역(시험항목/기준/결과) 원문 |
| action, office | 조치, 처리기관 |
| period_start, period_end | 검사지시 기간 |
| edited_fields | 담당자가 고친 칸 목록 |

**CustomerMatch — 고객사 판단 결과**

| 칸 | 설명 |
|---|---|
| item_id, customer_id | customer_id는 가명 ID(C001 등) |
| ai_matched / final_matched | bool |
| rule | maker, hs_code, origin_food_type, food_type_parent, food_type_only |
| confidence | high, medium |
| reason | 사람이 읽는 근거 문장 (예: "원산지 '영국' + 식품유형 '위스키' 일치 (A사 키워드)") |

**LawChange — 법령 개정 항목**

| 칸 | 설명 |
|---|---|
| id | `law:{행정규칙일련번호}` 등 |
| law_name, kind | 법령·고시명, 법령/행정규칙 |
| change_type | 제정, 일부개정, 전부개정, 폐지 |
| number | 고시·공포 번호 |
| promulgated_at, effective_at | 공포·고시일, 시행일 |
| articles | 주요 개정 조항 (원문) |
| ai_summary / final_summary | 개정 요지 |
| source_url | 출처 링크 |
| crosscheck | match, api_only, notice_only, not_checked + 메모 |
| related_food_types | 관련 식품유형(고객사 표시용) |

**WeeklyReport — 주간 보고서**

| 칸 | 설명 |
|---|---|
| run_id, period_start, period_end, week_label | 보고 기간, "2026년 11월 2주차" |
| section1_items | 부적합·검사지시 항목 + 관련 고객사 |
| section2_items | LawChange 목록 (없으면 "해당 없음") |
| section3_tip | 오늘의 팁 (P2, 없으면 생략 가능 여부 확인 필요) |
| status | draft, confirmed |

**MailDraft — 메일 초안**

| 칸 | 설명 |
|---|---|
| id, run_id | |
| kind | staff_summary(담당자용), customer(고객사별) |
| customer_id | customer일 때 |
| subject, ai_body, final_body | |
| warnings | 출처 누락, 다른 고객사명 포함, 원문에 없는 숫자 등 |
| status | draft, approved, sent |
| approved_by, approved_at, sent_at, gmail_draft_id, gmail_message_id | |

**EvalResult — 검증 결과**

| 칸 | 설명 |
|---|---|
| run_id, golden_week | 비교한 과거 보고서 주차 |
| selection_recall, selection_precision | 선별 재현율·정밀도 |
| match_recall, match_precision | 고객사 판단 재현율·정밀도 |
| review_needed_ratio | 검토 필요 비율 |
| missed_items, extra_items, wrong_matches | 목록 + 원인 태그 |
| elapsed_sec | 처리 시간 |

### 5-6. b1 → b2 인터페이스와 재실행 규칙

- b1은 `GET /api/b1/runs/{run_id}/result`로 `WeeklySelection`(선별·추출·고객사 판단 결과 + `LawChange` 목록)을 내보낸다.
- b2는 이 응답만 쓴다. **b1 코드를 import하지 않는다.**
- b1이 준비되기 전에는 `samples/b1_output/*.json`(LSH가 관리, 1일차는 KHS가 가짜 데이터로 작성)으로 개발한다.

| 담당자가 바꾼 것 | 다시 실행하는 단계 | 덮어쓰지 않는 것 |
|---|---|---|
| 선별 결과 | 추출 → 고객사 판단 → 보고서 → 초안 | 모든 `final_*` |
| 추출 칸 | 고객사 판단 → 보고서 → 초안 | 같음 |
| 고객사 판단 | 보고서 → 초안 | 같음 |
| 법령 요약 | 보고서 → 초안 | 같음 |
| 고객사 설정 | 고객사 판단 → 보고서 → 초안 | 같음 |
| 메일 본문 | 없음 | 재생성해도 `final_body` 유지, "AI 초안 바뀜" 표시 |

---

## 6장. API

prefix: `/api/core`(KHS), `/api/b1`(LSH), `/api/b2`(KHW). 라우터 등록은 `main.py`에서 1일차에 끝낸다.

| 메서드 | 경로 | 설명 | ID |
|---|---|---|---|
| GET | /api/core/health | 상태·LLM 사용 여부 (로그인 없이 호출 가능) | C-01 |
| POST | /api/core/auth/login | 로그인 `{username, password}` → 세션 토큰 (로그인 없이 호출 가능) | C-08 |
| POST | /api/core/auth/logout | 로그아웃 | C-08 |
| GET | /api/core/auth/me | 로그인한 사용자 확인 | C-08 |
| GET | /api/core/ai/status | AI 연결 상태(꺼짐·키 없음·연결 확인 전·연결됨·연결 실패), 지금 AI 회사·모델, 모델 목록. 키 값은 돌려주지 않는다 | C-02 |
| PUT | /api/core/ai/settings | AI 회사·모델 선택 `{provider, model}` 저장 | C-02 |
| POST | /api/core/ai/test | 연결 검사(모델 목록 조회만, 토큰 비용 없음) | C-02 |
| GET | /api/core/connections | 외부 연결 목록과 상태(AI·Supabase 읽기·쓰기·구글 드라이브·Gmail·법제처). 키·토큰 값은 돌려주지 않는다 | C-01 |
| POST | /api/core/connections/{conn_id}/test | 그 연결만 다시 검사(읽기만, 1건 조회). 결과는 `data/connections.json` | C-01 |
| POST | /api/core/runs | 주간 실행 만들기 `{reference_date}` → 보고 기간 계산 | C-06 |
| GET | /api/core/runs/{run_id}/status | 단계별 진행 현황 (현황 화면·단계 바 공용) | C-06 |
| GET | /api/core/runs/{run_id}/notices | 알림 목록(법령 개정·통관단계 검사지시) + 읽음·지움 상태 (제안) | C-06 |
| PATCH | /api/core/notices/{notice_id} | 알림 읽음·지움 `{action: "read" \| "dismiss"}`, 기록자는 로그인 사용자 (제안) | C-06 |
| POST | /api/b1/runs/{run_id}/upload | 수동 업로드 (source 지정) | B1-01 |
| POST | /api/b1/runs/{run_id}/collect | 자동 수집 (출처 선택) | B1-02~07 |
| POST | /api/b1/runs/{run_id}/analyze | 선별 → 추출 → 고객사 판단 | B1-08~11 |
| GET | /api/b1/runs/{run_id}/items | 항목·선별·추출 (`?label=`) | B1-08 |
| PATCH | /api/b1/items/{item_id}/selection | 선별 수정 → 하위 재실행 | B1-08 |
| PATCH | /api/b1/items/{item_id}/extracted | 추출 수정 → 하위 재실행 | B1-09 |
| GET | /api/b1/runs/{run_id}/matches | 고객사 판단 | B1-11 |
| PATCH | /api/b1/matches/{item_id}/{customer_id} | 판단 수정 | B1-11 |
| POST | /api/b1/runs/{run_id}/law | 법령 개정 수집·요약·대조 | B1-12~14 |
| GET | /api/b1/runs/{run_id}/law | 법령 개정 목록 | B1-13 |
| PATCH | /api/b1/law/{law_id} | 요약 수정 | B1-13 |
| GET | /api/b1/runs/{run_id}/result | b2용 결과(`WeeklySelection`) | 인터페이스 |
| GET/PUT | /api/b1/settings/sources | 출처 설정 | B1-15 |
| GET | /api/b1/settings/customers | 고객사 키워드(가명 ID로) | B1-15 |
| POST | /api/b2/runs/{run_id}/report | 보고서 조립 | B2-01 |
| PUT | /api/b2/runs/{run_id}/report/reannounce | 새 개정이 없는 주에 섹션 2에 넣을 법령 재안내 글 저장 | B2-01 |
| POST | /api/b2/runs/{run_id}/drafts | 메일 초안 생성 | B2-02,03 |
| GET | /api/b2/runs/{run_id}/drafts | 초안 목록 | B2-04 |
| PATCH | /api/b2/drafts/{draft_id} | 본문 수정 | B2-04 |
| POST | /api/b2/drafts/{draft_id}/gmail-draft | Gmail 초안함에 저장 | B2-05 |
| POST | /api/b2/drafts/{draft_id}/approve | 담당자 승인 | B2-05 |
| POST | /api/b2/drafts/{draft_id}/send | 발송 (승인 없으면 409) | B2-05 |
| POST | /api/b2/eval | 과거 보고서 비교 | B2-06 |
| GET | /api/b2/runs/{run_id}/eval | 검증 결과 | B2-06 |

---

## 7장. AI 호출 규칙

1. **호출 위치:** `core/llm.py`의 함수만 쓴다. 다른 파일에서 `anthropic`, `openai`를 import하지 않는다.
2. **구조화 출력:** 결과는 항상 JSON. 받은 뒤 Pydantic 모델로 검증한다. 검증 실패 시 **1회만 재시도**하고, 또 실패하면 `review_needed` + "AI 결과 형식 오류"로 남긴다.
3. **프롬프트 파일:** `backend/prompts/<b1|b2>/<이름>.v<N>.md`. 고칠 때는 새 버전 파일을 추가하고(`classify.v2.md`), 어떤 버전을 쓸지는 config에 적는다. 결과에 사용한 프롬프트 버전을 저장한다.
4. **고객사명 가리기:** 고객사 정보가 들어가는 호출은 `masking.mask()` → 호출 → `masking.unmask()`. 고객사 매칭 자체는 **규칙 기반이 먼저**이고 LLM은 보조다.
5. **보내는 것:** 공개 원문은 보내도 된다. 고객사 리스트·키워드는 가명 ID로만 보낸다.
6. **숫자·날짜:** LLM 출력의 숫자·날짜·고시번호가 원문에 없으면 경고(`warnings`)를 단다.
7. **끄기:** `LLM_ENABLED=false`면 LLM을 부르지 않고 규칙 결과만 쓴다.
8. **기록:** 호출마다 모델, 프롬프트 버전, 토큰 수, 소요 시간을 로컬 로그에 남긴다(비용 확인용).
9. **화면에 AI 상태 표시:** AI를 쓰는 탭(수집·선별, 고객사 판단, 법령 개정, 보고서·메일, 설정)은 제목 아래에 `components/ui/AiStatusBar.tsx`를 둔다. 상태 배지 + AI 회사·모델 선택 + [연결 검사] 버튼. 선택은 한 곳에 저장되어 모든 탭에 같이 적용된다.
10. **AI 회사·모델 선택:** 우선순위는 화면에서 고른 값(`data/ai_settings.json`, 커밋 안 함) > `.env`의 `AI_PROVIDER`·`OPENAI_MODEL`·`CLAUDE_MODEL` > `backend/config/ai_models.json` 첫 항목. 모델 목록은 `ai_models.json` 기본 목록에 연결 검사 때 받아 온 실제 목록을 더한다. 목록에 없는 모델은 "직접 입력"으로 넣는다.
11. **키:** `OPENAI_API_KEY`·`ANTHROPIC_API_KEY`는 `.env`에만 둔다. 화면·API 응답·로그에 키 값을 내보내지 않는다("키 있음/없음"만).
12. **연결 설정 화면(`/connections`):** AI와 다른 외부 연결(Supabase·구글 드라이브·Gmail·법제처)을 한 화면에 모은다. 연결마다 상태 배지 + [연결 검사], AI는 회사·모델 선택까지. 키를 넣거나 고친 뒤 [연결 검사]로 다시 확인한다. 검사는 읽기만 하고 쓰기·발송·토큰 소모를 하지 않는다.

---

## 8장. 데이터 수집 규칙

| 출처 | 방식 | 1주차(P0) | 이후(P1) | 비고 |
|---|---|---|---|---|
| 정보마루 부적합 | 목록 화면 읽기 (공개 API 없음, 기존 도구 확인) | 수동 업로드 | `impfood_unfit.py` | 기존은 `srchClassCd=6`(기구)만. 식품 분류 코드 확인 필요 |
| 정보마루 통관단계 검사지시 | 화면 읽기(예정) | 수동 업로드 | `impfood_inspection.py` | 화면 형식 확인 필요 |
| 정보마루 관련법령·정책소식 | 게시판 읽기(예정) | 수동 업로드 | `impfood_law_policy.py` | |
| 식약처 제개정고시 | 게시판 읽기(예정) | 수동 업로드 | `mfds_notice.py` | |
| 경인청 수입검사 뉴스레터 | 게시판 또는 Gmail 수신 | 수동 업로드 | `gyeongin_newsletter.py` | 받는 경로 확인 필요 |
| 법제처 API | OPEN API (`LAW_API_OC`, 등록 IP만) | `law_api.py` | 같음 | 대상 법령 목록 확인 필요 |
| Gmail 수신 | Gmail API (`GMAIL_INBOX_QUERY`) | — | `gmail_inbox.py` | 공문 발신처 확인 필요 |

공통 규칙(자세히는 RULES.md 6장): 사이트 하나 = 파일 하나, 한 출처가 실패해도 다른 출처는 계속, 요청 간격 `COLLECT_DELAY_SEC`, 이용약관·robots.txt 확인 후 자동 수집, 실패한 출처는 화면에 "수집 실패 → 수동 업로드" 표시.

출처별로 어느 보고서 섹션에 쓰는지는 `config/b1/sources.json`에 둔다(SAMC 전달 대기).

**근거 확인용 참고 출처** (수집 대상이 아니라 법령 요약·오늘의 팁 근거를 확인할 때 쓰는 곳, 팀 컨텍스트 문서 기준): 국가법령정보센터(식품등의 표시기준, 한시적 기준 및 규격 인정 기준, 부당한 표시·광고 내용 기준, 식품표시광고법·시행령·시행규칙, 주세법 시행령 별표), 식품분야 공전 온라인 서비스(식품·식품첨가물·기구용기포장·건강기능식품 공전), 식품안전나라(식품원료목록), 식약처 식품유형 분류원칙, 친환경 인증관리 정보시스템. 법령 개정 대상 목록(`config/b1/sources.json`의 `law_targets`, 제안)을 정할 때도 이 목록에서 시작하고 SAMC 확인을 받는다.

---

## 9장. 환경 변수

이름과 설명은 [`.env.example`](.env.example)이 기준이다. 값은 `.env`에만 넣고 커밋하지 않는다.

| 묶음 | 변수 |
|---|---|
| 실행 | APP_ENV, API_HOST, API_PORT, CORS_ORIGINS, TZ_NAME, DATA_DIR, LOCAL_DB_PATH |
| AI | LLM_ENABLED, AI_PROVIDER, ANTHROPIC_API_KEY, CLAUDE_MODEL, OPENAI_API_KEY, OPENAI_MODEL, MASK_CUSTOMER_NAMES |
| 구글 | GOOGLE_CREDENTIALS_FILE, GOOGLE_TOKEN_FILE, DRIVE_CUSTOMERS_FOLDER_ID, DRIVE_REPORTS_FOLDER_ID, DRIVE_LAW_FOLDER_ID, GMAIL_INBOX_QUERY, GMAIL_SENDER, GMAIL_STAFF_TO, MAIL_SEND_ENABLED |
| 공공 데이터 | LAW_API_OC, DATA_GO_KR_SERVICE_KEY, FOODSAFETY_API_KEY, COLLECT_USER_AGENT, COLLECT_DELAY_SEC |
| Supabase | SUPABASE_URL, SUPABASE_ANON_KEY(publishable 키), SUPABASE_SERVICE_ROLE_KEY(secret 키, PM만). 확인 위치는 5-2-1 |
| 로그인 | ADMIN_USERNAME, ADMIN_PASSWORD, AUTH_SECRET_KEY, AUTH_SESSION_HOURS |
| 화면 | `frontend/.env.local`: NEXT_PUBLIC_API_BASE (비밀값 금지) |

---

## 10장. 개발 순서

| 단계 | 기간 | 내용 | 완료 기준 |
|---|---|---|---|
| 0 | 1일차 | KHS 뼈대: 4-1 트리 전체 폴더·빈 파일, `main.py`·`b1_select/router.py`·`b2_mail/router.py` 라우터 등록, 사이드바·단계 바(DESIGN.md 1-0), `schema.py`, `period.py`, `schema.sql`, 로그인(C-08), 샘플 JSON | 로그인 화면 → 로그인 후 사이드바 3개 + 설정, 빈 화면 7개 열림, `/api/core/health` 응답 |
| 1 (P0) | 1주차 | 수동 업로드 → 선별 → 추출 → 고객사 판단 → 법령 API 요약 → 보고서 → 메일 초안 | 지난주 가짜·공개 자료로 메일 초안까지 화면에서 확인 |
| 2 (P1) | 2주차 | 자동 수집기, crosscheck, Gmail 초안·승인·발송, 검증 화면 | 과거 보고서 1주치로 지표 계산 |
| 3 (P2) | 여유 시 | 오늘의 팁, 정확도 고도화 | |
| 4 | 마지막 | exe 변환 | 다른 PC에서 실행 |

---

## 11장. 열린 질문

**자료 미수령**
- [ ] 과거 주간 보고서·메일 예시와 작성 기준 (기존 도구 주석에 "2026-11 2주차 예시 메일" 언급만 있음)
- [ ] 고객사 리스트와 "원산지-식품유형" 키워드 원본·형식
- [ ] 섹션별 출처 사이트 매핑 (SAMC 전달 대기 → `sources.json`)
- [ ] 11/24 미팅 정리 원문(PM 작성, 8장 기능 2·9장 일정·10장 확인 필요): 이 문서는 전달받은 팀 결정 사항으로 대신 썼다. 원문을 받으면 다시 대조한다
- [ ] 과거 주간 검역 소식 메일 약 10건(미팅 사전 질문 7-⑦): 같은 주 원본 소식과 함께 받아야 B2-06 검증이 가능하다

**SAMC 확인**
- [ ] 법령 API 결과가 식약처가 매주 올리는 공문과 일치하는지, 공문은 어느 메일·게시판으로 오는지
- [ ] 출처별 이용약관·자동 수집 가능 여부 (정보마루는 공개 API 없음)
- [ ] 정보마루 부적합 목록의 식품 분류 코드 전체, 통관단계 검사지시 화면 형식
- [ ] HS 코드 매칭: 공개 부적합 목록에 HS 코드 칸이 없음. 어디서 HS를 가져오는지, HS 개정 시 처리
- [ ] 법령 개정 대상 법령·고시 목록 (기존 도구는 기구 고시 2개만. 수입식품 전체 목록은 최신본 확인 필요)
- [ ] 보고 규칙을 기존 도구대로 쓸지: 실행 요일(기존 금요일 17:00), 지난주/이번 주, "새로 시행된 개정만", 행정예고 제외
- [ ] 식물·위생용품 정보의 출처
- [ ] 메일 구성(담당자 1통 + 고객사별), 수신자 그룹, 발송 계정
- [ ] 관련 고객사만이 아니라 모든 고객사에 공통으로 보내는 정보가 있는지(미팅 사전 질문 6-3)
- [ ] 출처를 처음부터 모두 연결해야 하는지, 핵심 출처부터 넓혀도 되는지(미팅 사전 질문 6-1)
- [ ] 오늘의 팁이 없을 때 섹션 3을 빼는지, "해당 없음"으로 두는지
- [ ] 보고서·화면 용어: "검역" vs "수입신고 검사"
- [ ] 성과지표(선별 정확도, 고객사 판단 정확도, 처리 시간)와 최종 검수 담당자

**기술·운영**
- [ ] 구글 인증 방식: exe 안에 인증 정보를 어떻게 둘지, 회사 비즈니스 계정의 OAuth 허용 여부
- [ ] Supabase에 공개 정보만 두는 방식에 대한 회사 동의
- [ ] exe 변환 방식
- [ ] Python 3.12와 기존 도구(3.15) 코드 이식 호환
- [ ] 법제처 API 등록 IP (PC마다 등록 필요)
- [ ] 저장소 공개 범위 (현재 public)
- [ ] 로그인 계정: 지금은 관리자 1개. 담당자별 계정·권한(승인·발송 가능자 구분)이 필요한지 SAMC 확인

---

## 12장. 용어 빠른 참조

| 용어 | 뜻 | 코드 이름 |
|---|---|---|
| 부적합 | 수입검사에서 기준·규격에 맞지 않아 판정된 건 (정보마루 공개 목록) | unfit |
| 통관단계 검사지시 | 특정 국가·품목을 통관 단계에서 정밀검사하도록 한 지시 (법적 근거 조항 확인 필요) | inspection_order |
| 제개정고시 | 식약처 고시의 제정·개정 | law_change |
| 시행일 | 개정 내용이 효력을 갖는 날. 보고 기준일 | effective_at |
| 식품유형 | 식품공전상 분류 (예: 위스키, 과실주) | food_type |
| 원산지(제조국) | 제품을 만든 나라 | origin_country |
| 고객사(화주) | SAMC가 수입 통관을 맡는 회사. 문서에서는 A사, B사 | customer |
| 원산지-식품유형 키워드 | 고객사별 관심 조합 (예: A사 – 위스키, 과실주, 일반증류주) | keywords |
| 관련 / 무관 / 검토 필요 | 선별 결과 | relevant / irrelevant / review_needed |
| 해당 없음 | 그 주에 섹션 내용이 없을 때 쓰는 고정 문구 | — |
| 보고 주차 | 보고 기간 월요일이 속한 달의 주차 | week_label |

---

## 13장. 작업 요청 프롬프트 (복사해서 사용)

**KHS — 1일차 뼈대**
```
AGENTS.md 0장과 4장, RULES.md 4장 "KHS 1일차 세팅 순서"를 따른다.
4-1 트리의 모든 폴더와 빈 파일(__init__.py, 빈 router.py·service.py, 빈 페이지)을 만든다.
backend/app/main.py에 core·b1·b2 라우터 등록, b1_select/router.py·b2_mail/router.py에 하위 라우터 전부 등록,
core/schema.py에 5-5의 모델 8종, core/period.py에 보고 기간·주차 계산, core/storage/schema.sql에 5-4 테이블,
frontend/app/layout.tsx에 DESIGN.md 1-0 사이드바·맨 위 줄·알림 종, samples/b1_output/sample_week.json(가상 고객사 A사·B사)을 만든다.
각 화면은 빈 페이지만. 끝나면 0-10 완료 기준을 확인하고 바꾼 파일 목록을 보고한다.
```

**LSH — 선별·고객사 판단 P0**
```
AGENTS.md 0장을 지킨다. 이번 작업은 기능 ID <B1-xx> 하나다. AGENTS.md 4-2 표에서 그 기능의 폴더·테스트·화면·화면 API 파일만 고친다.
(예: B1-11이면 backend/app/b1_select/match/, tests/b1/match/, frontend/app/customers/, lib/api/b1/match.ts)
P0 연결 순서는 B1-01(collect/sources/manual_upload.py) → B1-08(classify/) → B1-09(extract/) → B1-11(match/)이고, 연결은 b1_select/pipeline.py에서 한다.
고객사 판단 규칙은 match/rules/에 규칙 1개 = 파일 1개로 두고, config/b1/customers/sample_*.json 키워드로 매칭한다. 판단마다 match/reason.py로 근거 문장을 남긴다.
LLM은 core/llm.py만 쓰고 프롬프트는 prompts/b1/classify.v1.md. 애매하면 review_needed.
테스트는 tests/b1에 가상 데이터로. DB 칸이 더 필요하면 고치지 말고 나에게 알려라.
```

**LSH — 법령 개정**
```
AGENTS.md 0-6을 지킨다. 고칠 곳은 backend/app/b1_select/law/, tests/b1/law/, frontend/app/law/, lib/api/b1/law.ts뿐이다.
law/law_api.py는 기존 도구 law_data/law_api.py의 search_admrul·admrul_detail 방식을 따른다.
보고 기간은 core/period.py를 쓰고, law/new_in_force.py는 그 기간에 "새로 시행된" 개정만 고르고, law/reported.py로 이미 보고한 개정은 뺀다.
law/summarize.py는 LawChange를 만든다.
법령명·번호·시행일·조항은 API 원문에서만 채우고, 없으면 None("확인 필요"). 요지만 LLM으로 요약한다.
```

**KHW — 보고서·메일 초안 P0**
```
AGENTS.md 0장을 지킨다. 이번 작업은 기능 ID <B2-xx> 하나다. AGENTS.md 4-2 표에서 그 기능의 폴더·테스트·화면·화면 API 파일만 고친다.
b1 결과는 b2_mail/input.py로만 읽고, b1이 준비되기 전에는 samples/b1_output/sample_week.json을 쓴다.
B2-01은 b2_mail/report/(섹션 파일 3개), B2-02·03은 b2_mail/draft/staff.py·customer.py, 경고 검사는 draft/checks.py에 둔다.
양식은 DESIGN.md 10장. 섹션 2가 비면 "해당 없음". 숫자·날짜는 입력 JSON 값만 쓰고,
고객사 메일에 다른 고객사 이름이 들어가면 warnings에 남긴다. 발송 기능은 만들지 않는다.
```

**KHW — 검증**
```
B2-06을 만든다. 고칠 곳은 backend/app/b2_mail/evaluate/(golden.py·align.py·metrics.py), tests/b2/evaluate/, frontend/app/evaluate/, lib/api/b2/evaluate.ts뿐이다.
samples/past_reports/의 정답 표와 이번 결과를 항목 단위로 맞춰
선별 재현율·정밀도, 고객사 판단 재현율·정밀도, 검토 필요 비율을 계산하고 누락·과다 목록과 원인 태그를 남긴다.
```

**막혔을 때**
```
지금 막힌 문제: <증상>. 관련 파일: <경로>. 시도한 것: <내용>.
AGENTS.md 0장 범위 안에서 원인 후보 3개와 확인 방법을 먼저 말하고, 코드는 내가 고르면 고쳐라.
내 폴더 밖 파일이 원인이면 고치지 말고 누구에게 무엇을 요청해야 하는지 알려라.
```

**리뷰 요청**
```
이 PR diff를 RULES.md 3장 체크리스트와 AGENTS.md 0장 기준으로 검토해라.
담당 폴더 밖 수정, 고객사 실명, ai_/final_ 덮어쓰기, 근거 없는 숫자·날짜, 서버 기능 사용을 우선 찾아라.
```
