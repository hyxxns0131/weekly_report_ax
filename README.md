# weekly_report — 수입식품 주간 검역 보고서 작성 프로그램

> 상태: 초안 · 작성일: 2026-11-24 · KITA 무역 AX마스터 2기 최종 프로젝트 2조 · 관세법인 SAMC 기업연계
> 기준 자료: 기업 제안서 5·6번, 11/24 SAMC 미팅 합의, SAMC 기존 도구(customs_bot)

**매주 손으로 쓰던 수입식품 주간 검역 보고서를, 공개 정보 수집부터 고객사별 안내 메일 초안까지 자동으로 준비한다. 최종 확인과 발송은 담당자가 한다.**

## 해결하려는 문제

| 지금 | 프로그램이 하는 일 |
|---|---|
| 매주 여러 사이트(수입식품정보마루, 식약처 제개정고시, 경인청 뉴스레터, 법제처)를 직접 돌며 자료를 찾는다 | 출처별 수집을 한 화면에 모은다 |
| 국내식품·의약품·화장품 등 무관한 소식을 사람이 걸러낸다 | 수입식품 관련 / 무관 / 검토 필요로 분류하고 사유를 붙인다 |
| 법령이 수시로 바뀌어 개정 반영이 빠지기 쉽다 | 법제처 API로 새로 시행된 개정을 찾고, 식약처 주간 공문과 대조한다 |
| 어느 고객사와 관련 있는지 경험으로 판단한다 | 고객사 "원산지-식품유형" 키워드·HS 코드·제조사로 관련 고객사를 찾고 근거를 남긴다 |
| 메일을 매주 새로 쓴다 | 매주 같은 틀의 담당자용·고객사별 메일 초안을 만든다 |

## 문서

| 문서 | 내용 |
|---|---|
| [AGENTS.md](AGENTS.md) | AI 코딩 도구 기준 문서: 기능 목록, 구조, 데이터, API, AI 규칙, 열린 질문 |
| [RULES.md](RULES.md) | 브랜치·커밋·PR, 충돌 방지, 코드·보안·도메인 규칙 |
| [DESIGN.md](DESIGN.md) | 화면 설계, 보고서·메일 양식 |
| [CLAUDE.md](CLAUDE.md) | AI 도구 연결 파일 (AGENTS.md를 읽게 함) |
| [.env.example](.env.example) | 환경 변수 이름과 설명 (값은 `.env`에만) |
| `docs/` | 이관·사용 방법(`handover/`), 담당자별 작업 노트(`b1/`, `b2/`) |

## 업무·담당

| 번호 | 담당 | 기능 (기능 ID) | 화면 | 폴더 |
|---|---|---|---|---|
| 5 | LSH | 수집(B1-01~07), 관련/무관/검토 필요 분류(B1-08), 정보 추출(B1-09), 식품유형 정규화(B1-10), 관련 고객사 판단(B1-11), 법령 개정 수집·요약·공문 대조(B1-12~14), 설정(B1-15) | 재료 준비(자료 모으기·선별·정보 뽑기·고객사 판단·법령 정리), 설정 | `backend/app/b1_select/<기능>/`, `frontend/app/{collect,customers,law,settings}` |
| 6 | KHW | 보고서 조립(B2-01), 메일 초안·수정 이력(B2-02~04), Gmail 초안·승인·발송·보관(B2-05·08), 검증(B2-06), 오늘의 팁(B2-07) | 보고서·메일(보고서 조립·메일 초안·승인·발송·검증) | `backend/app/b2_mail/<기능>/`, `frontend/app/{drafts,evaluate}` |
| 공통 | KHS (PM) | 공통 스키마·라우터·사이드바·단계 바(C-01), LLM(C-02), 고객사명 가리기(C-03), DB·저장소(C-04), 구글 인증(C-05), 이번 주 현황·알림(C-06), exe(C-07) | 이번 주 현황, 모든 화면의 사이드바·단계 바·알림 종 | `backend/app/core/`, `frontend/app/page.tsx`, `supabase/` |

기구·용기 검역 신고 리스트(제안서 1~4번)는 별도 저장소 `declaration_list`에서 만든다. 이 프로그램은 2순위다.

## 대표 시연 시나리오 (제안서 최종 산출물 ②)

1. **지난주 정보로 메일 초안까지**
   1. 이번 주 현황에서 [주간 실행 만들기] → 보고 기간(지난주 월~일) 자동 설정. 오른쪽 위 알림 종에서 이번 주 바뀐 점(법령 개정·통관단계 검사지시)을 먼저 읽기
   2. 재료 준비 ①~③: 자료 모으기(수집 또는 올리기) → 선별(관련 / 무관 / 검토 필요) → 정보 뽑기
   3. 재료 준비 ④ 고객사 판단: 부적합·검사지시마다 관련 고객사와 근거 확인
   4. 재료 준비 ⑤ 법령 정리: 새로 시행된 개정 요약과 공문 대조 결과 확인 (없으면 "해당 없음") → [재료 넘기기]
   5. 보고서·메일 ①~③: 보고서 조립 → 담당자용 1통 + 고객사별 초안 확인·수정 → 승인 → (시연에서는 Gmail 초안함 저장까지)
2. **검증:** 과거 실제 보고서와 비교한 선별 누락·과다, 고객사 판단 정확도 표

시연에는 가상 고객사(A사, B사)와 공개 정보만 쓴다.

## 폴더

팀원이 많아 **기능 ID 하나 = 폴더 하나**로 나눴다. 기능 하나를 맡으면 그 폴더와 짝 파일(테스트·프롬프트·화면·화면 API)만 고치므로 서로 충돌하지 않는다.

```
weekly_report/
├─ AGENTS.md  RULES.md  DESIGN.md  README.md  CLAUDE.md        KHS
├─ .github/  .gitattributes  .gitignore  .env.example          KHS
├─ backend/
│  ├─ requirements/   base.txt (KHS) · b1.txt (LSH) · b2.txt (KHW)
│  ├─ app/
│  │  ├─ main.py                  KHS 고정 (라우터 3개)
│  │  ├─ core/                    KHS  config · schema(고정) · period · llm · masking · gmail_client · storage/ · runs/
│  │  ├─ b1_select/               LSH  제안서 5번
│  │  │  ├─ router.py  pipeline.py  result.py
│  │  │  ├─ collect/              B1-01~07  sources/ 출처 1개 = 파일 1개
│  │  │  ├─ classify/             B1-08     관련 / 무관 / 검토 필요
│  │  │  ├─ extract/              B1-09     정보 추출
│  │  │  ├─ food_type/            B1-10     식품유형·국가 정규화
│  │  │  ├─ match/                B1-11     고객사 판단, rules/ 규칙 1개 = 파일 1개
│  │  │  ├─ law/                  B1-12~14  법령 개정 수집·요약·공문 대조
│  │  │  └─ settings/             B1-15     출처·고객사 키워드 설정
│  │  └─ b2_mail/                 KHW  제안서 6번
│  │     ├─ router.py  input.py
│  │     ├─ report/               B2-01     보고서 조립 (섹션 파일 3개)
│  │     ├─ draft/                B2-02~04  담당자용·고객사별 초안, 경고, 수정 이력
│  │     ├─ send/                 B2-05·08  Gmail 초안·승인·발송·보관
│  │     ├─ evaluate/             B2-06     과거 보고서 대비 검증
│  │     └─ tips/                 B2-07     오늘의 팁
│  ├─ prompts/b1 (LSH) · prompts/b2 (KHW)
│  ├─ templates/ (KHW)   config/b1 (LSH) · config/b2 (KHW)
│  └─ tests/core (KHS) · tests/b1/<기능> (LSH) · tests/b2/<기능> (KHW)
├─ frontend/                      Next.js (정적 export)
│  ├─ app/layout.tsx (KHS 고정: 사이드바 3개 + 설정, 알림 종) · page.tsx 현황 (KHS)
│  ├─ app/collect · customers · law · settings   LSH
│  ├─ app/drafts · evaluate                      KHW
│  ├─ components/ui/                             KHS
│  └─ lib/api/client.ts·core.ts (KHS) · lib/api/b1/<기능>.ts (LSH) · lib/api/b2/<기능>.ts (KHW) · lib/types/
├─ samples/   b1_output · b1_input (LSH) · past_reports (KHW, 비식별)
├─ supabase/migrations/   scripts/   docs/handover/      KHS
├─ docs/b1 (LSH) · docs/b2 (KHW)
└─ data/                          로컬 DB (커밋 안 함)
```
파일 단위 전체 트리와 기능 ID → 폴더 표는 [AGENTS.md 4장](AGENTS.md#4장-저장소-구조), 파일 주인은 [RULES.md 4-2](RULES.md#4-2-파일-소유표).

## 실행 방법 (제안, 뼈대가 만들어진 뒤 확정)

### 준비
1. Python 3.12, Node.js LTS 설치
2. `.env.example`을 복사해 `.env`를 만들고 값을 채운다. **`.env`는 커밋하지 않는다.**
   ```
   copy .env.example .env
   ```
3. 구글 클라우드에서 OAuth 데스크톱 앱 `credentials.json`을 받아 맨 위 폴더에 둔다(커밋 금지). 처음 실행 때 브라우저 로그인 → `token.json` 자동 생성.
4. `.env`의 `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `AUTH_SECRET_KEY`를 채운다. 프로그램을 열면 첫 화면이 로그인이고, 이 계정으로 들어간다.
5. 법제처 OPEN API(`LAW_API_OC`)는 **등록한 공인 IP에서만 동작**한다. 내 PC IP를 등록해야 한다.

### backend
```
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements/base.txt -r requirements/b1.txt -r requirements/b2.txt
uvicorn app.main:app --reload --port 8000
```
확인: http://127.0.0.1:8000/api/core/health

### frontend
```
cd frontend
copy .env.local.example .env.local
npm ci
npm run dev
```
확인: http://localhost:3000

### 테스트
```
cd backend && pytest && ruff check .
cd frontend && npx tsc --noEmit && npm run build
```

## 처음 시작하는 팀원

1. `git clone https://github.com/hyxxns0131/weekly_report.git` → `git switch <내 이니셜>` → `git pull origin dev`
2. `copy .env.example .env` 후 필요한 값만 채운다.
   - `SUPABASE_URL`은 이미 적혀 있다. `SUPABASE_ANON_KEY`에는 KHS에게 1:1로 받은 **publishable 키**(`sb_publishable_…`)를 넣는다.
   - `SUPABASE_SERVICE_ROLE_KEY`는 비워 둔다(KHS만, secret 키). 팀원 키로는 Supabase 읽기만 된다.
   - 키 위치(KHS용): Supabase 대시보드 → `weekly-report-ax` → Project Settings → API Keys. 자세히는 [AGENTS.md 5-2-1](AGENTS.md).
3. [AGENTS.md 4-2](AGENTS.md#4-2-기능-id--폴더-빠른-찾기)에서 내 기능 ID의 폴더를 확인한다. 그 폴더와 짝 파일만 고친다.
4. AI 도구에 일을 시킬 때는 [AGENTS.md 13장](AGENTS.md#13장-작업-요청-프롬프트-복사해서-사용) 프롬프트를 복사해 쓴다.
5. 커밋·PR은 사람이 직접 한다. AI 도구에게 커밋·push·PR을 시키지 않는다.
6. 하루 작업 순서와 충돌이 났을 때 할 일은 [RULES.md 4-5·4-6](RULES.md#4-5-하루-작업-순서).

## 브랜치 요약

`main`(최종, PM만) ← `dev`(통합·기본 브랜치) ← `KHS` / `LSH` / `KHW`. PR은 **dev ← 내 브랜치**. 매일 `git pull origin dev`로 시작. 모든 PR은 PM(KHS)이 직접 승인·머지한다. 자세히는 [RULES.md 1~4장](RULES.md).

## 이관 산출물 (제안서 4. 기업 이관)

| 산출물 | 위치 |
|---|---|
| 소스코드·Git 링크 | 이 저장소 (https://github.com/hyxxns0131/weekly_report) |
| 외부 API·DB 이름과 설정값 이름 | `.env.example`, AGENTS.md 9장 (값은 전달 시 별도) |
| 설정 파일 형식 | `config/b1/sources.json`, `scope.json`, `food_types.json`, `customers/sample_*.json`, `config/b2/mail.json` → `docs/handover/`에 설명 |
| 표준 로직·규칙 목록 | RULES.md 11장 |
| SAMC 기존 도구와의 연계 방안 | `docs/handover/` (기존 `law_data/import_failures.py`, `law_api.py`, `drive_export.build_weekly`와의 관계) |
| 사용 방법 | `docs/handover/사용방법.md` |

## 기존 도구(customs_bot)와의 관계

SAMC 기존 도구에는 **기구·용기포장에 한정된** 주간 보고 자료 기능이 있다(부적합 목록 + 새로 시행된 기구 고시 개정 → 드라이브 문서 → Gemini 스킬이 초안). 이 프로그램은 그 구조(보고 기간, 3섹션, 중복 보고 방지)를 이어받아 **수입식품 전체**로 넓히고, 관련 고객사 판단과 메일 초안·승인·검증을 더한다.
