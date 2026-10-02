# QA-Native 테스트 케이스 작성 가이드

> **문서 유형: 작성 매뉴얼** · Markdown TC 형식과 작성 규칙. 웹에서 작성하는 절차는 [TC 스튜디오 사용자 설명서](tc-studio/TC_AUTHORING_USER_GUIDE.md)를 참고합니다.

> **독자**: 사람 — 테스트케이스 작성 규칙. 에이전트가 읽지 않음.

QA-Native 파이프라인용 테스트 케이스 작성 가이드입니다.
모든 케이스 파일은 이 가이드를 따라 일관성 있게 작성되어야 합니다.

---

## 처음 한 건을 작성하는 순서

웹에서 입력하고 싶다면 [TC 스튜디오 설명서](tc-studio/TC_AUTHORING_USER_GUIDE.md)를 사용합니다. 이 가이드는 Markdown 파일을 직접 작성하거나 내보낸 문서를 검토할 때 사용합니다.

1. 검증할 화면과 조건 **한 가지**를 정합니다. 예: 이름을 비우고 등록하면 이름 입력 안내가 표시되는가.
2. 시작 조건을 적습니다. 다른 필수 항목은 정상 상태여야 이름 조건만 확인할 수 있습니다.
3. 사용자가 할 행동을 순서대로 적습니다.
4. 마지막으로 관찰할 결과를 적습니다. 어떤 문구가 어디에 표시되고 다음 화면으로 이동하는지 등을 구체적으로 씁니다.
5. 아래 예처럼 필수 메타데이터와 본문을 한 파일에 저장합니다.
6. 그룹의 URL과 TC의 대상 화면이 같은지 확인합니다.

### 바로 읽어 볼 수 있는 한 건의 예

아래는 가상의 회원 등록 화면에 대한 예시입니다. 실제 제품에 적용하기 전 UI 문구와 준비 조건을 바꿉니다. 파일 이름 예는 `testcases/member_registration/tc_01_name_required.md`입니다.

```markdown
---
id: tc_01
data_key: null
priority: high
tags: [negative, validation]
type: structured
---
# 이름 미입력 안내 표시

## Precondition
0. 회원 등록 화면을 열고 이메일과 약관 동의는 정상 입력 상태로 준비한다.

## Steps
1. 이름 입력란을 비운다.
2. 등록 버튼을 누른다.

## Expected
- 등록이 진행되지 않는다.
- 이름 입력란 아래에 "이름을 입력하세요." 문구가 표시된다.
```

`data_key: null`은 이 문서에서 별도로 참조할 테스트 데이터셋이 없다는 뜻입니다. 준비 조건에 실제 계정이나 입력 데이터가 필요하다면 테스트 데이터셋을 만들고 `data_key`와 Step의 참조를 맞춥니다.

### 한 케이스로 묶을지 나눌지 판단

| 작성하려는 내용 | 판단 |
|---|---|
| 이름 미입력 시 안내와 등록 차단 확인 | 같은 조건에서 함께 나오는 결과이므로 한 케이스로 작성 가능 |
| 이름 미입력과 이메일 형식 오류를 각각 확인 | 조건이 다르므로 별도 케이스 |
| 정상 등록 후 로그인과 회원 탈퇴까지 확인 | 검증 목적이 여러 개이므로 목적별로 분리 |
| 같은 동작을 다른 문장으로 두 번 작성 | 중복 여부를 확인하고 하나로 정리 |

제목은 확인할 목적, Step은 수행할 행동, Expected는 관찰할 결과입니다. Step에 “오류가 표시되는지 확인한다”만 적고 Expected를 비우면 실제로 무엇을 수행해야 하는지 불명확합니다.

## 파일 규칙

- **형식**: Markdown (`.md`)
- **위치**: `testcases/{그룹명}/tc_{번호}_{설명}.md` 또는 `tc_{그룹코드}_{번호}_{설명}.md`
  - 그룹코드: 그룹을 나타내는 알파벳 약자 (예: `CL`=customer_login, `PL`=partner_login)
- **1파일 = 1케이스**: 파일 하나에 테스트 케이스 하나
- **그룹명**: 기능 단위 폴더 (예: `login`, `mypage`, `signup`)
- **템플릿**: [`templates/tc-template.md`](../../templates/tc-template.md) 참조

```
testcases/
  login/
    tc_01_login_success.md           ← 순번만 사용하는 기본 형식
    tc_02_wrong_password.md
  customer_login/
    tc_CL_01_빈_필드_유효성_검증.md   ← 그룹코드 포함 형식
    tc_CL_02_잘못된_자격증명_에러.md
  partner_login/
    tc_PL_01_협력사_로그인_빈_필드.md
    tc_PL_02_협력사_잘못된_자격증명.md
```

**실제 프로젝트 사례**: 각 파일이 독립적인 Python 테스트 파일(`tc_CL_01_...py`, `tc_PL_02_...py`)로 변환되어 `tests/generated/{그룹}/`에 저장됨.

---

## 케이스 파일 형식

YAML frontmatter + Markdown 본문으로 구성한다.

```markdown
---
id: "CL_01"
data_key: valid_user
priority: high
tags: [positive, smoke]
type: structured
---
# 케이스 제목

## Precondition
0. 시작 조건

## Steps
1. username 필드에 test_data[valid_user].username 입력
2. password 필드에 test_data[valid_user].password 입력
3. Login 버튼 클릭

## Expected
- 기대 결과
```

> **`id` 형식**: `tc_{번호}` (기본) 또는 `"{그룹코드}_{번호}"` (그룹코드 포함).
> 그룹코드 포함 ID는 문자열임을 명확히 하도록 따옴표로 감싸는 것을 권장함 (예: `id: "CL_01"`, `id: "PL_02"`).

---

## Frontmatter 필드

파일 최상단 `---` 블록 안에 메타데이터를 기록한다.

| 필드 | 필수 | 값 | 설명 |
|------|------|-----|------|
| `id` | **필수** | `tc_{번호}` 또는 `"{그룹코드}_{번호}"` | 케이스 고유 식별자. 그룹코드 포함 시 따옴표로 감싸기 (예: `"CL_01"`, `"PL_02"`) |
| `data_key` | **필수** | `{프로덕트}.{데이터셋}` \| `null` | test_data/{프로덕트}.json 안의 {데이터셋} 키. 점이 없으면 그룹 폴더명을 프로덕트로 본다 |
| `priority` | **필수** | `very_high` \| `high` \| `medium` \| `low` | 우선순위 (very_high = 차단급 핵심 흐름, TC 스튜디오 P0) |
| `tags` | **필수** | 배열 `[유형, 분류]` | 테스트 유형 태그 |
| `type` | **필수** | `structured` \| `natural` | 케이스 형식 |

추가 frontmatter 키 `source_ref`는 TC 스튜디오가 쓰는 출처다 (`tc-library:{스위트}/{case_id}`). 파서는 보존만 하고 파이프라인은 쓰지 않는다.

### 유형 태그 (tags)

| 태그 | 설명 |
|------|------|
| `positive` | 정상 동작 확인 |
| `negative` | 비정상 입력/실패 시나리오 |
| `smoke` | 핵심 기능 빠르게 확인 |
| `auth` | 인증/로그인 관련 |
| `validation` | 입력값 검증 |
| `security` | 보안 취약점 확인 |
| `edge_case` | 경계값/특수 상황 |
| `session` | 세션 관리 |
| `navigation` | 페이지 이동 |
| `content` | 콘텐츠/텍스트 확인 |

### data_key 규칙
- `{프로덕트}.{데이터셋}` → `test_data/{프로덕트}.json` 안의 `{데이터셋}` 키. 점이 없으면 그룹 폴더명을 프로덕트로 본다
- Steps에서 `test_data[{프로덕트}][{데이터셋}].{속성}` 형식으로 참조
- 입력값이 필요 없는 케이스는 `null`

---

## 우선순위 (Priority)

| 등급 | 기준 |
|------|------|
| **very_high** | 차단급 핵심 흐름 — TC 스튜디오 P0 |
| **high** | 핵심 기능 — 서비스 접근, 로그인, 주요 플로우 |
| **medium** | 보조 기능 — 유효성 검증, 에러 처리 |
| **low** | 엣지케이스 — 특수문자, 경계값, 대소문자 등 |

---

## 언어 규칙

- **기본 언어**: 한글
- **영어 사용**: UI 요소명, 버튼명, 입력값, 기술 용어
  - O: `Login 버튼 클릭`, `username 필드에 test_data[valid_user].username 입력`
  - X: `로그인 버튼 클릭`, `사용자이름 필드에 값 입력`
- **화면 표시 텍스트 번역 금지**: 실제 UI에 보이는 문자 그대로 사용
  - O: `You logged into a secure area!`, `Your password is invalid!`
  - X: `로그인 성공 메시지`, `비밀번호가 틀립니다`

---

## 필수 필드 (4개)

| 필드 | 필수 | 설명 |
|------|------|------|
| 제목 (`#`) | **필수** | TC Summary — 테스트 목적 한줄 요약 |
| `## Precondition` | **필수** | 테스트 시작 전 시스템 상태 |
| `## Steps` | **필수** | 실행 단계 목록 (순서대로) |
| `## Expected` | **필수** | 기대 결과 |

---

## 필드별 작성 규칙

### 제목 (`#`)

- 무엇을 검증하는지 한눈에 파악 가능해야 함
- 15자 이내 간결하게

```markdown
# 정상 로그인 성공          ← Good
# 잘못된 비밀번호 오류 확인  ← Good
# 앱을 처음 설치했을 때 정상적으로 동작하는지 확인하는 테스트  ← Bad (너무 김)
```

---

### Precondition

- `0.` 으로 시작 (Step과 구분)
- 테스트 시작 직전 시스템 상태를 간결하게 명시

```markdown
## Precondition
0. 로그인 페이지 접속 상태       ← Good
0. 앱 미설치 상태                ← Good

## Precondition
앱이 설치되어 있어야 함          ← Bad (0. 형식 미준수)
```

---

### Steps

- `1.`, `2.`, `3.` 번호로 순서 명시 **(권장)**
- 번호 없는 평문 줄도 파서가 지원하나, 가독성과 일관성을 위해 번호 형식 사용을 권장
- 각 step = **단일 액션** (입력 or 클릭 or 이동 하나씩)
- 입력값은 `test_data[{프로덕트}][{데이터셋}].{속성}` 형식으로 참조 (하드코딩 금지)

```markdown
## Steps
1. username 필드에 test_data[valid_user].username 입력    ← Good
2. password 필드에 test_data[valid_user].password 입력
3. Login 버튼 클릭

## Steps
1. username 필드에 testuser 입력   ← Bad (하드코딩)
2. 로그인 정보 입력 후 Login 클릭   ← Bad (복수 액션을 하나에 묶음)
```

---

### Expected

- `-` 항목으로 검증 포인트 명시
- 실제 화면에 표시되는 **구체적 텍스트, 상태, UI 요소** 기재

```markdown
## Expected
- You logged into a secure area! 메시지가 표시되어야 한다.   ← Good
- Your password is invalid! 오류 메시지가 표시되어야 한다.   ← Good

## Expected
- 정상 동작함    ← Bad (검증 기준 없음)
- 에러 없음      ← Bad (구체적 상태 없음)
```

---

## 실제 케이스 예시

```markdown
---
id: "CL_01"
data_key: valid_user
priority: high
tags: [positive, smoke]
type: structured
---
# 정상 로그인 성공

## Precondition
0. 로그인 페이지 접속 상태

## Steps
1. username 필드에 test_data[valid_user].username 입력
2. password 필드에 test_data[valid_user].password 입력
3. Login 버튼 클릭

## Expected
- You logged into a secure area! 플래시 메시지가 표시되어야 한다.
```

```markdown
---
id: "CL_08"
data_key: sql_injection
priority: medium
tags: [security, negative]
type: structured
---
# SQL Injection 시도 차단 확인

## Precondition
0. 로그인 페이지 접속 상태

## Steps
1. username 필드에 test_data[sql_injection].username 입력
2. password 필드에 test_data[sql_injection].password 입력
3. Login 버튼 클릭

## Expected
- 로그인이 실패하고 오류 메시지가 표시되어야 한다. (보안 우회 불가)
```

---

## Quality Checklist

케이스 작성 완료 전 확인사항:

- [ ] 파일명이 `tc_{번호}_{설명}.md` 또는 `tc_{그룹코드}_{번호}_{설명}.md` 형식으로 작성됨
- [ ] **YAML frontmatter**가 파일 최상단에 있음 (`---` 블록)
- [ ] frontmatter 필수 필드 5개: `id`, `data_key`, `priority`, `tags`, `type`
- [ ] **priority**가 `very_high` / `high` / `medium` / `low` 중 하나
- [ ] **data_key**가 `test_data/{프로덕트}.json`에 {데이터셋} 키가 있음 (또는 `null`)
- [ ] Steps 입력값이 `test_data[{프로덕트}][{데이터셋}].{속성}` 형식 (하드코딩 금지)
- [ ] 제목이 테스트 목적을 명확하게 표현함 (15자 이내)
- [ ] `Precondition`이 `0.` 으로 시작함
- [ ] `Steps`가 단일 액션씩 작성됨 (번호 형식 `1.`, `2.` 권장; 평문도 파서 지원)
- [ ] `Expected`가 `-` 항목으로 구체적 텍스트/상태를 명시함 ("정상 동작" 금지)
- [ ] 화면 UI 텍스트가 실제 표시 언어의 원문 그대로 사용됨
- [ ] 하나의 파일에 하나의 케이스만 있음


## 저장 후 다시 읽는 방법

첫 작성이 끝나면 다음 순서로 문서를 다시 읽습니다.

1. **제목만 읽기**: 어떤 조건을 검증하는지 다른 케이스와 구별되는가?
2. **사전 조건 읽기**: 다른 사람이 같은 시작 상태를 준비할 수 있는가?
3. **Step 따라 읽기**: 버튼·입력란 이름과 순서가 실제 화면과 일치하는가?
4. **Expected 읽기**: 성공·실패를 눈으로 판별할 기준이 있는가?
5. **데이터 참조 확인**: data_key에 적은 제품·데이터셋과 Step에서 참조한 키가 같은가?
6. **저장 위치 확인**: 한 파일에 한 케이스만 있으며 그룹과 대상 URL이 일치하는가?

### 모호한 문장을 고치는 예

| 수정 전 | 수정 후 예 | 바꾼 이유 |
|---|---|---|
| 정상 동작한다 | 등록 완료 화면으로 이동하고 완료 안내가 표시된다 | 관찰할 화면과 결과를 명시 |
| 오류 확인 | 등록 버튼을 누른다 / Expected: 이름 입력 안내가 나타난다 | 행동과 기대 결과를 분리 |
| 값 입력 | 이메일 입력란에 지정한 테스트 데이터의 이메일을 입력한다 | 입력 대상과 데이터 출처를 명시 |
| 적당히 긴 이름 | 기획에 명시된 최대 길이와 경계값을 사용한다 | 임의의 기준으로 검증하지 않도록 함 |

### 기존 문서를 수정할 때

조건이 바뀌었다면 Step뿐 아니라 사전 조건·Expected·UI 문구를 함께 확인합니다. 제목만 바꿔 서로 다른 조건을 같은 TC로 섞지 않습니다. TC 스튜디오에서 내보낸 파일이라면 라이브러리와 자동 동기화되지 않으므로 라이브러리에서 수정하고 다시 내보내는 방식을 우선 사용합니다.
