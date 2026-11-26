# RULES.md — 협업·Git·도메인 규칙 (weekly_report)

> 상태: 초안 · 작성일: 2026-11-24 · 기준 자료: 팀 결정 사항(11/24), 기업 제안서 5·6번, SAMC 기존 도구(customs_bot) `AGENTS.md`·`.gitignore`·`law_data/*`
> AI 작업 기준은 [AGENTS.md](AGENTS.md), 화면·양식은 [DESIGN.md](DESIGN.md)에 있다. 이 문서는 사람과 AI가 함께 지키는 규칙이다.
> 1~3장, 5장, 9~10장은 `declaration_list` 저장소와 **공통**이다. 이 저장소만 다른 점은 "weekly_report만" 표시로 적는다.

---

## 1. 브랜치

```
main            ← 최종 안정 버전 (PM만 반영, PR 승인 필수)
 └─ dev         ← 통합·테스트 (기본 브랜치, 팀원 PR이 모이는 곳)
     ├─ KHS     (PM)
     ├─ LSH     (5번, b1_select)
     └─ KHW     (6번, b2_mail)
```

- main·dev에 직접 push하지 않는다. (예외: 1일차 뼈대는 PM이 dev에 직접 올릴 수 있다)
- 처음 한 번: `git clone https://github.com/hyxxns0131/weekly_report.git` → `git switch <내 이니셜>`
- 매일 시작: `git switch <내 이니셜>` → `git pull origin dev`
- 작업 후: `git add <내 폴더>` → `git commit` → `git push origin <내 이니셜>` → GitHub PR **base: dev ← compare: <내 이니셜>**
- PM: PR 확인 후 dev 머지 → dev에서 실행 확인 → 문제 없으면 dev → main PR 승인·머지
- 충돌은 혼자 해결하지 말고 공유한다. 특히 `core/`, `main.py`, `layout.tsx`.

## 2. 커밋

형식: `<타입>(<범위>): <요약>` (요약은 한국어, 50자 이내)

| 타입 | 쓰는 때 |
|---|---|
| feat | 기능 추가 |
| fix | 버그 수정 |
| ui | 화면만 바꿈 |
| refactor | 동작은 같고 구조만 바꿈 (요청받았을 때만) |
| docs | 문서 |
| chore | 설정·의존성·빌드 |
| db | 테이블·마이그레이션 (PM만) |
| test | 테스트만 |

범위(weekly_report만): `collect`, `select`, `extract`, `match`, `law`, `report`, `mail`, `evaluate`, `tips`, `core`, `ui`, `db`, `docs`

예: `feat(match): 원산지-식품유형 키워드 매칭 추가` · `fix(law): 시행 예정 개정이 섞이는 문제 수정`

- 한 커밋에 한 가지 일만.
- 커밋 메시지에 고객사 실명·API 키를 쓰지 않는다.

## 3. Pull Request

### 3-1. 템플릿 (`.github/pull_request_template.md` 전문)

```markdown
## 무엇을 바꿨나
- 제안서 항목: 5번 / 6번 / 공통   ·  기능 ID: (예: B1-11)
- 구분: [재사용] / [개선] / [신규]
- 요약:

## 확인 방법
- 실행한 명령:
- 화면에서 볼 곳:

## 스크린샷 (화면을 바꿨으면)

## AI가 정한 설계 결정
- (AI 코딩 도구가 스스로 정한 이름·구조·라이브러리·기본값을 적는다. 없으면 "없음")

## 변경 요청 (내 폴더 밖 / KHS 고정 파일 / DB)
- (필요한 칸·함수·라우터·메뉴를 적는다. 없으면 "없음")

## 체크리스트
- [ ] 내 담당 폴더만 고쳤다
- [ ] KHS 고정 파일(main.py, core/schema.py, layout.tsx, schema.sql, supabase/migrations)을 고치지 않았다
- [ ] 고객사 실명·API 키·.env·token.json이 없다
- [ ] ai_* 와 final_* 를 나눠 저장하고, 재실행이 final_* 를 덮어쓰지 않는다
- [ ] 법령·숫자·날짜에 출처가 있고, 없으면 "확인 필요"로 둔다
- [ ] 메일은 승인 없이 발송되지 않는다
- [ ] 화면에 서버 기능(API Routes·Server Actions·SSR·middleware)을 쓰지 않았다
- [ ] pytest / ruff / tsc / npm run build 통과
```

### 3-2. 머지 조건
- **모든 PR은 PM(KHS)이 직접 검토하고 승인·머지한다.** 팀원끼리 승인·머지하지 않는다.
- 머지 전 완료 기준(AGENTS.md 0-10) 통과가 필요하다.
- KHS 본인의 PR도 KHS가 직접 머지한다. (GitHub은 자기 PR 승인을 막으므로, main 보호 규칙에서 관리자 우회를 허용해 둔다)
- dev → main도 KHS만 한다.

### 3-3. 크기
- 바뀐 줄이 **400줄을 넘으면 나눈다.** (샘플 JSON·자동 생성 파일 제외)
- 하루 한 번 이상 작게 올린다.

## 4. 충돌 방지 규칙 (팀 합의)

### 4-1. 원칙
1. **모든 파일에 주인이 1명이다.** 남의 파일을 고쳐야 하면 먼저 그 주인에게 말하고, PR 설명 "변경 요청"에 적고, 그 사람을 리뷰어로 넣는다. 승인·머지는 KHS가 한다.
2. **여럿이 손대는 파일은 KHS가 1일차에 빈 칸까지 미리 만들고 고정한다.** 라우터 등록(`main.py`, `b1_select/router.py`, `b2_mail/router.py`), 화면 메뉴(`layout.tsx`), 공통 스키마(`core/schema.py`). 바꿀 일이 있으면 PR 설명 "변경 요청" 칸에 적는다.
3. **기능 ID 단위로 나눈다.** 기능 하나 = 백엔드 폴더 하나 + 테스트 폴더 하나 + 화면 API 파일 하나. 수집기는 출처 1개 = 파일 1개, 고객사 판단 규칙은 규칙 1개 = 파일 1개. 새 출처·규칙은 새 파일로 추가하고 기존 파일은 건드리지 않는다.
4. **프롬프트는 고치지 않고 새 버전을 추가한다.** `classify.v1.md` → `classify.v2.md`.
5. **b1과 b2는 공통 스키마와 샘플 JSON(`samples/b1_output/`)으로만 주고받는다.** KHW는 LSH 작업을 기다리지 않고 샘플로 개발한다. b2에서 b1 코드를 import하지 않는다.
6. **`.gitattributes`로 줄바꿈을 통일한다.** 매일 `git pull origin dev`로 시작하고, `git add`는 자기 폴더만 한다(`git add .` 금지).

### 4-2. 파일 소유표

기능 단위 상세 경로는 [AGENTS.md 4-1·4-2](AGENTS.md#4-1-전체-트리-주인--기능-id). **기능 하나를 맡으면 그 기능 폴더와 짝 파일(테스트·프롬프트·설정·화면·화면 API)만 고친다.** 같은 사람이라도 다른 기능 폴더는 다른 PR로 올린다.

**문서·설정 (KHS)**

| 경로 | 주인 | 남이 고칠 때 |
|---|---|---|
| `AGENTS.md`, `RULES.md`, `DESIGN.md`, `README.md`, `CLAUDE.md` | KHS | PR 설명에 변경 요청 |
| `.github/`, `.gitattributes`, `.gitignore`, `.env.example` | KHS | 변경 요청 |
| `scripts/`, `docs/handover/` | KHS | 변경 요청 |

**고정 파일 (1일차 뒤 누구도 직접 고치지 않음)**

| 경로 | 주인 | 바꿀 때 |
|---|---|---|
| `backend/app/main.py` (core·b1·b2 라우터 3개) | KHS | 변경 요청만 |
| `backend/app/core/schema.py` | KHS | 변경 요청 → KHS 반영 → LSH·KHW 둘 다 확인 |
| `backend/app/core/storage/schema.sql`, `supabase/migrations/` | KHS (DB, PM만) | 변경 요청만 |
| `backend/app/b1_select/router.py` (하위 라우터 7개) | LSH | 1일차 뒤 고정. 엔드포인트는 기능 폴더 `router.py`에 |
| `backend/app/b2_mail/router.py` (하위 라우터 5개) | KHW | 1일차 뒤 고정. 엔드포인트는 기능 폴더 `router.py`에 |
| `frontend/app/layout.tsx` (사이드바 3개 + 설정, 맨 위 줄, 알림 종) | KHS | 변경 요청만 |

**백엔드 기능 폴더**

| 경로 | 기능 ID | 주인 |
|---|---|---|
| `core/config.py`, `period.py`, `llm.py`, `masking.py`, `gmail_client.py`, `storage/` 나머지, `runs/` | C-01~06 | KHS |
| `core/auth/` | C-08 로그인 | KHS |
| `b1_select/pipeline.py`, `result.py` | 연결·b2 인터페이스 | LSH |
| `b1_select/collect/` (`sources/` 출처 1개 = 파일 1개) | B1-01~07 | LSH |
| `b1_select/classify/` | B1-08 | LSH |
| `b1_select/extract/` | B1-09 | LSH |
| `b1_select/food_type/` | B1-10 | LSH |
| `b1_select/match/` (`rules/` 규칙 1개 = 파일 1개) | B1-11 | LSH |
| `b1_select/law/` | B1-12~14 | LSH |
| `b1_select/settings/` | B1-15 | LSH |
| `b2_mail/input.py` | b1 결과 읽기 | KHW |
| `b2_mail/report/` | B2-01 | KHW |
| `b2_mail/draft/` | B2-02~04 | KHW |
| `b2_mail/send/` | B2-05·08 | KHW |
| `b2_mail/evaluate/` | B2-06 | KHW |
| `b2_mail/tips/` | B2-07 | KHW |

**백엔드 짝 파일**

| 경로 | 주인 | 나누는 단위 |
|---|---|---|
| `backend/prompts/b1/`, `config/b1/` | LSH | 프롬프트 1개 = 파일 1개(새 버전 추가), 설정 1종 = 파일 1개 |
| `backend/prompts/b2/`, `templates/`, `config/b2/` | KHW | 같음. 템플릿 섹션은 `templates/parts/` 파일 1개씩 |
| `backend/tests/conftest.py`, `tests/core/` | KHS | |
| `backend/tests/b1/<기능>/` | LSH | 백엔드 기능 폴더와 같은 이름 |
| `backend/tests/b2/<기능>/` | KHW | 같음 |
| `backend/requirements/base.txt` | KHS | 변경 요청 |
| `backend/requirements/b1.txt` / `b2.txt` | LSH / KHW | 9장 절차 |

**화면**

| 경로 | 주인 | 비고 |
|---|---|---|
| `frontend/app/page.tsx` (이번 주 현황), `app/login/` (로그인), `app/connections/` (연결 설정) | KHS | |
| `frontend/app/collect/`, `customers/`, `law/`, `settings/` | LSH | `_components/`에 기능별 부품 파일 (예: `UploadPanel.tsx`, `ClassifyTable.tsx`) |
| `frontend/app/drafts/`, `evaluate/` | KHW | 같음 (예: `ReportPreview.tsx`, `DraftEditor.tsx`, `SendPanel.tsx`) |
| `frontend/components/ui/` | KHS | 변경 요청. 바꿀 때는 LSH·KHW 둘 다 리뷰어로 (모든 화면에 영향). 단계 바(`StepBar.tsx`·`steps.ts`)와 알림(`NoticeBell.tsx`·`NoticePopup.tsx`)도 여기 |
| `frontend/lib/api/client.ts`, `core.ts`, `lib/types/core.ts` | KHS | `types/core.ts`는 `schema.py`와 같게 |
| `frontend/lib/api/b1/<기능>.ts`, `lib/types/b1.ts` | LSH | `collect·classify·extract·match·law·settings` |
| `frontend/lib/api/b2/<기능>.ts`, `lib/types/b2.ts` | KHW | `report·drafts·send·evaluate·tips` |
| `frontend/package.json`, `package-lock.json`, `next.config.ts` | KHS | 9장 절차 (다른 사람은 `npm ci`만) |

**샘플·문서**

| 경로 | 주인 | 비고 |
|---|---|---|
| `samples/b1_output/`, `samples/b1_input/` | LSH (1일차 초안은 KHS) | 스키마가 바뀌면 LSH가 갱신 |
| `samples/past_reports/` | KHW | 비식별 |
| `docs/b1/` / `docs/b2/` | LSH / KHW | 작업 노트·조사 |

### 4-3. KHS 1일차 세팅 순서
한 번에 올리고(커밋·PR은 KHS가 직접), 팀원은 그 위에서 시작한다.

1. 빈 폴더와 빈 파일: AGENTS.md 4-1 트리의 모든 폴더, `__init__.py`, 기능 폴더마다 빈 `router.py`·`service.py`·세부 파일, `tests/` 기능 폴더, 빈 페이지 7개, `lib/api/b1/*.ts`·`b2/*.ts` 빈 파일
2. `main.py`: `/api/core`, `/api/b1`, `/api/b2` 라우터 등록 (이후 고정)
3. 로그인(C-08): `core/auth/`, `app/login/page.tsx`, `layout.tsx`의 로그인 확인, `client.ts`의 토큰 붙이기, `main.py`에서 b1·b2 라우터에 `require_login` 걸기
4. `b1_select/router.py`: collect·classify·extract·match·law·settings·result 하위 라우터 7개 등록, `b2_mail/router.py`: report·draft·send·evaluate·tips 하위 라우터 5개 등록 (이후 고정)
5. `layout.tsx`: 사이드바 3개(이번 주 현황·자료 선별·고객사 매칭·보고서·메일) + 맨 아래 설정, 맨 위 줄(보고 주차·알림 종), `components/ui/StepBar.tsx`·`steps.ts` (이후 고정, DESIGN.md 1-0)
6. `core/schema.py`: AGENTS.md 5-5 모델 8종 (이후 고정), `lib/types/core.ts` 같은 모양
7. `core/period.py`: 보고 기간·주차 계산
8. `core/storage/schema.sql`: AGENTS.md 5-4 테이블
9. `samples/b1_output/sample_week.json`: 가상 고객사 A사·B사, 부적합 3건·검사지시 1건·법령 개정 1건
10. `requirements/base.txt`, `b1.txt`, `b2.txt`(빈 파일), `frontend/package.json`
11. 확인: `uvicorn app.main:app` → `/api/core/health`, `npm run build` 성공

### 4-4. 충돌이 나기 쉬운 곳과 막는 방법

| 파일 | 왜 충돌하나 | 막는 방법 |
|---|---|---|
| `main.py`, `b1_select/router.py`, `b2_mail/router.py` | 모두가 라우터를 등록하려 함 | 1일차에 하위 라우터를 전부 등록해 두고 고정. 엔드포인트는 기능 폴더 `router.py`에만 |
| `core/schema.py`, `lib/types/core.ts` | 모두가 칸을 추가하려 함 | KHS만 고친다. 변경 요청 → KHS가 한 PR로 반영 → 모두 `git pull origin dev` |
| `layout.tsx`(사이드바), `components/ui/steps.ts`(단계 목록) | 화면을 늘릴 때마다 메뉴·단계 수정 | 사이드바 3개 + 설정과 단계 목록을 1일차에 고정. 단계 안 화면은 각자 `page.tsx`에서 `?step=`으로 나눈다 |
| `package.json`, `package-lock.json` | 각자 `npm install` 하면 lock 파일이 통째로 바뀜 | KHS만 설치. 다른 사람은 `npm ci`만 |
| `requirements/*.txt` | 같은 줄에 서로 다른 버전 추가 | b1·b2 파일 분리, `==` 고정, 알파벳 순으로 한 줄씩 |
| `samples/b1_output/*.json` | LSH 스키마 변경과 KHW 테스트가 동시에 바뀜 | LSH만 고친다. 바꿀 때 PR에 "샘플 바뀜"을 적고 KHW에게 알림 |
| `config/b1/*.json`, `config/b2/*.json` | 큰 JSON 한 파일을 여럿이 수정 | 설정 1종 = 파일 1개. 고객사는 `customers/<가명>.json` 파일 하나씩 |
| `prompts/` | 같은 프롬프트를 동시에 수정 | 고치지 않고 `v2` 파일 추가. 사용 버전은 각자 config에 |
| `__init__.py` | 여러 사람이 import를 추가 | 빈 파일로 둔다. 다른 모듈을 `__init__.py`에서 다시 내보내지 않는다 |
| `components/ui/` | 화면마다 부품을 고치고 싶어 함 | KHS만 고친다. 필요한 부품은 각자 `_components/`에 먼저 만들고, 두 화면 이상에서 쓰게 되면 KHS에게 공통화 요청 |
| 문서(md) | 여러 사람이 같은 장을 수정 | KHS만 고친다. 각자 노트는 `docs/b1/`, `docs/b2/` |

### 4-5. 하루 작업 순서

```
git switch <내 이니셜>
git pull origin dev                 # 시작 전에 항상
# ... 기능 폴더 하나만 작업 ...
git status                          # 내 폴더 밖 파일이 바뀌었으면 되돌린다
git add backend/app/b1_select/match/ backend/tests/b1/match/   # 예: B1-11. "git add ." 금지
git commit -m "feat(match): ..."
git pull origin dev                 # push 전에 한 번 더
git push origin <내 이니셜>
# GitHub에서 PR: base dev ← compare <내 이니셜>
```

- 하루 1번 이상 작게 올린다. 이틀 넘게 묵힌 브랜치는 충돌이 커진다.
- PR 하나 = 기능 ID 하나. 두 기능을 한 PR에 섞지 않는다.
- 내 PR이 머지되기 전에 같은 파일을 이어서 고쳐야 하면, 머지를 기다리거나 같은 PR에 커밋을 더한다.

### 4-6. 충돌이 났을 때

1. 혼자 해결하지 않는다. 충돌 난 파일과 상대 PR을 팀 채팅에 올린다.
2. **내 폴더 파일**이면: `git pull origin dev` 후 내 쪽에서 고치고 테스트를 다시 돌린다.
3. **남의 폴더·고정 파일**이면: 내 변경을 버리고(`git checkout origin/dev -- <파일>`) "변경 요청"으로 바꾼다.
4. `package-lock.json` 충돌은 손으로 고치지 않는다. dev 쪽을 받고(`git checkout origin/dev -- frontend/package-lock.json`) `npm ci`.
5. 해결한 뒤에는 0-10 완료 기준을 다시 확인하고 PR에 "충돌 해결: <파일>"을 적는다.

### 4-7. 다른 사람 결과가 필요할 때

| 필요한 것 | 기다리지 않고 하는 방법 |
|---|---|
| KHW가 b1 결과 필요 | `samples/b1_output/sample_week.json`으로 개발. `b2_mail/input.py`가 API와 샘플을 바꿔 읽는다 |
| LSH·KHW가 공통 함수 필요 (보고 기간, LLM, 가리기 등) | `core/`의 함수만 쓴다. 없으면 변경 요청. 같은 기능을 내 폴더에 따로 만들지 않는다 |
| 새 테이블·칸 필요 | 7장 절차. 반영 전에는 기존 칸 + 테스트용 가짜 데이터로 개발 |
| 화면에서 다른 담당 API 호출 | 그 담당의 `lib/api/<b1|b2>/<기능>.ts` 함수를 import만 한다. 고치지 않는다 |

## 5. 코드 규칙

### 5-1. Python
- Python 3.12, `ruff check`·`ruff format` 통과.
- 모든 함수에 타입 힌트. 데이터는 dict 대신 Pydantic v2 모델.
- 환경 변수는 `core/config.py`로만 읽는다(`os.getenv` 직접 호출 금지).
- 외부 호출(HTTP·LLM·Gmail)은 timeout을 둔다. 실패는 예외를 삼키지 말고 단계 결과에 "실패 + 이유"로 남긴다.
- 로그에 고객사 실명·메일 본문·API 키를 남기지 않는다.

### 5-2. TypeScript
- `strict: true`, `any` 금지(`unknown` + 타입 좁히기).
- API 응답 타입은 `lib/types/b1.ts`, `b2.ts`에 정의하고 화면은 그 타입만 쓴다.
- 화면에서 `fetch`를 직접 쓰지 않고 `lib/api/<b1|b2>/<기능>.ts`의 함수만 쓴다.

### 5-3. 파일 이름
- Python: `snake_case.py`. 화면 폴더: 소문자. 컴포넌트: `PascalCase.tsx`.
- 프롬프트: `<이름>.v<N>.md`. 마이그레이션: `YYYYMMDDHHMM_<내용>.sql`.

### 5-4. 화면 규칙 (자세한 화면 설계는 DESIGN.md)
- **서버 기능 금지:** API Routes(`app/api/`), Server Actions(`"use server"`), SSR·서버 컴포넌트 데이터 요청, `middleware.ts`를 쓰지 않는다. `next.config.ts`의 `output: "export"`를 유지한다.
- 데이터를 쓰는 화면 파일은 맨 위에 `"use client"`를 둔다. 데이터는 `useEffect` 등에서 `lib/api/*` 함수로 불러온다.
- 동적 경로(`[id]`)는 정적 export에서 제약이 있으므로 쓰지 않는다. 상세 보기는 같은 페이지 안 패널이나 `?id=` 쿼리로 한다.
- 한 화면 = 한 폴더. 기능별 부품은 `_components/<기능 이름>.tsx`로 나눈다(DESIGN.md 1-1).
- 공통 부품(`components/ui/`)과 색 토큰(`tokens.ts`)만 쓴다. 색을 직접 적지 않는다.
- 문구는 페이지 상단 `const TEXT = {…}`에 모은다. 빈 화면·불러오는 중·오류·정상 4가지 상태를 모두 보여 준다(DESIGN.md 11장).
- AI 결과에는 "AI 결과 · 담당자 확인 전" 배지를 붙인다.

## 6. 수집기 규칙

1. **사이트 하나 = 파일 하나** (`b1_select/collect/sources/`). 모든 수집기는 같은 반환 형식 `list[RawItem]`.
2. **한 사이트가 깨져도 다른 사이트는 돌아가게** 한다. 출처별 결과는 `ok / failed / manual`로 기록하고 화면에 보여 준다.
3. **요청 간격** `COLLECT_DELAY_SEC`(기본 2초), User-Agent는 `COLLECT_USER_AGENT`. 한 번 실행에 페이지 수 상한을 둔다(기존 도구 `MAX_PAGES = 6` 참고).
4. **이용약관·robots.txt를 먼저 확인**하고, 자동 수집이 안 되는 출처는 수동 업로드로 둔다. 확인 결과는 `config/b1/sources.json`의 `allowed` 칸에 적는다.
5. 공개 API가 있으면 화면 읽기보다 API를 쓴다. 정보마루 부적합은 공개 API가 없어 기존 도구도 목록 화면을 읽는다.
6. 사이트 구조가 바뀌어 파싱이 0건이면 "0건"이 아니라 **"수집 실패(구조 변경 의심)"**로 표시한다.
7. 원문은 가공 전 그대로 저장한다(`RawItem.body`). 추출·요약은 그다음 단계에서.
8. 법제처 API는 등록한 공인 IP에서만 동작한다. "사용자 정보 검증에 실패"면 OC·IP 문제로 안내한다.

## 7. DB 규칙 (PM만 관리)

- 로컬 테이블(`core/storage/schema.sql`)과 Supabase(`supabase/migrations/`)는 **KHS만** 만들고 고친다.
- 담당자는 `core/storage/local_db.py`, `public_db.py`의 함수로만 읽고 쓴다. SQL을 각자 모듈에 직접 쓰지 않는다.
- 변경 절차: 담당자가 PR "변경 요청"에 테이블·칸·이유를 적음 → KHS가 마이그레이션 추가 → dev 머지 → 담당자가 사용.
- 칸은 **추가만** 한다. 이름 변경·삭제는 회의로 정한다.
- 로컬 DB 파일(`data/weekly.db`)은 커밋하지 않는다. 스키마가 바뀌면 `python -m app.core.storage.local_db --init`(제안)으로 다시 만든다.
- Supabase 적재(서비스 키 사용)는 KHS만. 팀원 `.env`에는 `SUPABASE_SERVICE_ROLE_KEY`를 넣지 않는다.

### 7-1. Supabase 읽기·쓰기 나누기

| 누구 | 키 (대시보드 이름) | `.env` 변수 | 할 수 있는 것 |
|---|---|---|---|
| KHS (PM) | secret 키 `sb_secret_…` | `SUPABASE_SERVICE_ROLE_KEY` | 테이블 만들기·적재·수정·삭제 |
| LSH·KHW | publishable 키 `sb_publishable_…` | `SUPABASE_ANON_KEY` | 읽기(SELECT)만 |

- 키 확인: Supabase 대시보드 → 프로젝트 `weekly-report-ax` → **Project Settings → API Keys**. 팀원은 대시보드에 들어가지 않고 KHS에게 publishable 키를 1:1로 받는다.
- 모든 테이블은 RLS를 켜고 `SELECT` 정책만 둔다. INSERT·UPDATE·DELETE 정책은 만들지 않는다(쓰기는 secret 키로만).
- 키 값은 채팅방·이슈·PR·커밋·로그에 쓰지 않는다. 샜으면 KHS에게 바로 알리고, KHS가 새 키를 만들고 옛 키를 지운다.
- 고객사 서류 원본은 기업 보안 조건을 확인하고 **HS가 따로 승인하기 전까지** Supabase(테이블·Storage 모두)에 올리지 않는다.

## 8. 데이터·보안 규칙

### 8-1. 저장 3구분
| 저장소 | 넣는 것 |
|---|---|
| 구글 드라이브 | 고객사 목록·키워드, 확정 보고서, 발송 메일 |
| 로컬 SQLite | 작업 중 결과, 초안, 캐시 |
| Supabase | 공개 정보만 |

### 8-2. Supabase 금지 데이터
- 고객사명(실명·가명 ID 모두), 고객사 키워드·제품 리스트
- 고객사 판단 결과(`CustomerMatch`)
- 메일 본문·수신자 주소
- 담당자 이름·이메일
- 예외: 과거 보고서 정답용 비공개 표 `past_report`, `past_report_match`(RLS 켜고 정책 없음, secret 키만). PM 결정. AGENTS.md 5-1 참고

### 8-3. 고객사명 가리기
- LLM 호출 전 `core/masking.py`로 실명 → 가명 ID(C001…). 결과를 받은 뒤 되돌린다.
- 고객사 매칭은 로컬 규칙이 먼저다. LLM 보조에는 가명 ID와 키워드만 보낸다.

### 8-4. 커밋 금지
- `.env`, `frontend/.env.local`, `credentials.json`, `token.json`, `*.key`, `*.pem`
- `data/`, `*.db`, 실제 고객사 설정(`config/b1/customers/`의 `sample_*.json` 외)
- 원본 업무 자료(엑셀·PDF·hwp·eml): 비식별 자료만 `samples/`에
- **weekly_report만:** 이 저장소는 현재 공개(public)다. 비공개 전환 전까지 실제 자료는 절대 올리지 않는다.

### 8-4-1. 로그인 계정
- 관리자 아이디·비밀번호는 각자 PC의 `.env`(`ADMIN_USERNAME`, `ADMIN_PASSWORD`)에만 둔다. 채팅·문서·커밋·스크린샷에 쓰지 않는다.
- 팀원끼리 계정을 전달할 때는 메신저에 글자로 남기지 말고 직접 알려 준다. 바뀌면 `.env`만 고친다.
- `AUTH_SECRET_KEY`는 PC마다 아무 긴 문자열로 새로 만든다(예: `python -c "import secrets;print(secrets.token_urlsafe(32))"`).

### 8-5. 메일 발송 승인
- 순서: 초안 저장 → (선택) Gmail 초안함 저장 → **담당자 승인** → 발송.
- 발송 API는 `status=approved`이고 `approved_by`, `approved_at`이 있는 초안만 보낸다. 아니면 409.
- 승인 뒤 본문을 고치면 승인이 풀린다(`status=draft`).
- 예약·일괄·자동 발송 기능은 만들지 않는다.
- 발송한 메일은 드라이브(`DRIVE_REPORTS_FOLDER_ID`)에 보관한다.

## 9. 의존성 추가

1. PR 설명에 **이름·버전·이유·대안**을 적는다.
2. Python: 내 파일(`b1.txt`/`b2.txt`)에 `==`로 고정해 추가. 둘 다 쓰게 되면 KHS가 `base.txt`로 옮긴다.
3. npm: KHS에게 요청 → KHS가 `package.json`·`package-lock.json` 갱신. 다른 사람은 `npm ci`만 실행.
4. KHS가 승인해야 머지.

## 10. AI 코딩 도구 사용

- 작업 전 AI 도구가 `AGENTS.md`를 읽게 한다(`CLAUDE.md`가 연결).
- 요청은 AGENTS.md 13장 프롬프트를 복사해서 쓴다. 한 번에 한 작업.
- AI 도구는 커밋·push·PR을 하지 않는다. 파일 변경까지만 하고, 커밋과 PR은 본인이 직접 한다.
- AI가 정한 이름·구조·라이브러리는 PR "AI가 정한 설계 결정" 칸에 적는다.
- AI가 내 폴더 밖·고정 파일·DB를 고쳤으면 되돌리고 "변경 요청"으로 바꾼다.
- 고객사 자료·`.env` 내용을 AI 대화창에 붙여 넣지 않는다.

## 11. 도메인 규칙

### 11-1. 선별 기준 (제안서 수행범위·5번)
| 구분 | 내용 |
|---|---|
| 대상 (관련) | 수입식품(농·임·수·축산물, 가공식품), 식물, 위생용품의 수입 검사·통관 관련 정보 |
| 제외 (무관) | 국내식품, 의약품, 의약외품, 화장품, 접객업소 등 수입식품과 무관한 정보 |
| 검토 필요 | 국내·수입 공통 고시, 대상 판단이 애매한 것, AI 결과 형식 오류, LLM이 꺼진 상태 |

- 애매하면 무관으로 버리지 않고 **검토 필요**로 남긴다(누락 방지).
- 무관 항목도 지우지 않는다. 화면에서 접어 두고 사유를 보여 준다.
- 키워드 목록은 `config/b1/scope.json`. 키워드는 힌트일 뿐, 최종은 분류 + 담당자 확인.

### 11-2. 고객사 판단 규칙 (제안서 5번, 미팅 11/24)
판단 순서(규칙 기반 먼저, AI는 보조):

| 순서 | 조건 | 결과 | 신뢰도 |
|---|---|---|---|
| 1 | 고객사 수입 이력의 제조사와 같음 (표기 차이 정규화) | 관련 | high |
| 2 | HS 코드가 같은 제품 | 관련 | high |
| 3 | 원산지 + 식품유형이 키워드와 일치 | 관련 | high |
| 4 | 원산지 일치 + 식품유형이 상위 분류로만 일치 | 관련 | medium → 검토 필요 |
| 5 | 식품유형만 일치, 또는 "전 국가" 대상 검사지시 | 관련 후보 | medium → 검토 필요 |
| 6 | 그 외 | 무관 | — |

- 판단마다 **근거 문장**을 남긴다(예: "원산지 '영국' + 식품유형 '위스키' 일치 (A사 키워드: 위스키, 과실주, 일반증류주)"). 기존 도구 `import_failures.related`의 문장 형식을 따른다.
- **HS 코드 주의:** HS 코드는 개정될 수 있다. 비교할 때는 같은 기준 연도인지 확인하고, 다르면 검토 필요로 둔다. 공개 부적합 목록에는 HS 코드 칸이 없어 출처 확인 필요.
- 공개 목록에는 수입자가 없다. "우리 고객사가 수입했다"가 아니라 **"우리 고객사와 관련 있을 수 있다"**로 쓴다.

### 11-3. 법령 개정 요약 규칙
- 항목마다: **법령·고시명, 구분(제정·일부개정·전부개정·폐지), 번호, 공포·고시일, 시행일, 주요 개정 조항, 개정 요지, 출처 링크.**
- 법령명·번호·날짜·조항은 법제처 API·고시 원문에서만 채운다. 없으면 "확인 필요".
- 요지는 원문(제·개정 이유)을 근거로 요약하고, 원문 문장을 함께 보관한다.
- 기억에 의존한 내용에는 "최신본 확인 필요"를 붙인다.
- 기존 도구 규칙 이어받음(SAMC 확인 필요): **시행일 기준 "새로 시행된" 개정만** 넣고, 시행 예정은 넣지 않는다. 이미 보고한 개정은 다시 넣지 않는다(`reported_law`). 보고 기간 월요일 14일 전부터 시행된 것까지 본다.
- 대조(crosscheck): 법제처 API 결과와 식약처 주간 공문을 비교해 `match / api_only / notice_only`로 표시한다. 불일치는 담당자 확인 대상.

### 11-4. 보고 기간·주차
- 금·토·일 실행 → 이번 주(월~일), 월~목 실행 → 지난주(월~일). (기존 도구 규칙, SAMC 확인 필요)
- 제목 주차: 보고 기간 월요일이 속한 달에서 1일이 든 주를 1주차로 센다. 예: 2026년 11월 2주차.
- 부적합은 부적합일자 기준, 법령은 시행일 기준.

### 11-5. 보고서 고정 틀과 말투 (미팅 11/24)
- **매주 같은 틀.** 섹션 1 부적합·통관단계 검사지시 / 섹션 2 법령 개정 요약 / 섹션 3 오늘의 팁. 양식은 DESIGN.md 10장.
- **일반적인 말투**, 바로 복사해 보낼 수 있는 수준. 존댓말 평서문, 과장·추측 표현 금지.
- 섹션 2가 가장 중요하다. 내용이 없으면 **"이번 주 새로 시행된 관련 법령 개정 사항은 해당 없습니다."**처럼 "해당 없음"으로 안내한다(섹션 1도 같음).
- 모든 항목 끝에 출처를 붙인다.
- 고객사 메일에는 그 고객사 관련 항목만 넣고, 다른 고객사 이름이 들어가지 않게 한다.

## 12. 근거 표기

| 대상 | 표기 |
|---|---|
| 부적합·검사지시 | 출처명 + 원문 링크 + 게시(부적합)일 |
| 법령·고시 | 법령명, 번호, 시행일, 조항, 링크 |
| 고객사 판단 | 판단 규칙 + 근거 문장 |
| 오늘의 팁 | 근거 법령·고시·공전 항목 + 링크. 근거 없으면 쓰지 않는다 |
| 확인 못 한 것 | "확인 필요" |
| 기억에 의존한 것 | "최신본 확인 필요" |
