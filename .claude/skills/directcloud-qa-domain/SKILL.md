---
name: directcloud-qa-domain
description: DirectCloud 제품 특화 QA 전략. ACL 역할별 테스트, 데이터 소스 우선순위, 필수 테스트 영역 정의. TC 작성·코드 생성 전 참조.
origin: qa-native (CX-QA-AI senior-qa 이식)
---

# DirectCloud QA Domain

## 데이터 소스 우선순위

TC Expected Result의 사양 근거를 확인할 때 반드시 아래 순서로 검색한다:

```
① Obsidian Vault (/Users/songkyoungjin/Documents/Obsidian Vault/) — 최우선: 현행 확정 사양
② Web-Manual (공식 매뉴얼)                                        — 교차 검증용
③ 기타 참고 자료 (FAQ, EML, Backlog)                              — 참고용, 단독 인용 금지
```

> **주의**: 수치(용량, 개수, 시간 등)를 기대값에 명시할 때 반드시 Tier 1 소스(Vault)에서
> 최신값을 확인한다. 예: "업로드 최대 용량 30GB 초과 시 에러" → Vault에서 플랜별 제한을
> 확인 후 플랜별 테스트 케이스로 분리.

---

## 필수 테스트 영역

### ACL 권한 테스트 (모든 파일/폴더 관련 TC 필수)

| 역할 | 검증 항목 |
|------|----------|
| **관리자 (Admin)** | 전체 사용자 파일 접근, 권한 설정 변경, 정책 적용 |
| **일반 사용자** | 자신의 Box 접근, 공유된 폴더 접근, 권한 범위 내 조작 |
| **게스트** | 공유 링크 전용 접근, 다운로드 전용 시나리오 |

**검증 패턴**:
```python
# 권한 없는 사용자의 접근 거부 확인
page.goto(restricted_url)
page.wait_for_load_state('networkidle')
# 리다이렉트 또는 에러 페이지 확인
assert '/auth/' in page.url or '/error' in page.url or \
       page.locator('.error-message, .access-denied').is_visible()
```

### 파일 버전 관리

- 동일 파일명 업로드 시 버전 충돌 처리 확인
- 버전 이력 조회 및 이전 버전 복원
- 동시 편집 충돌 시나리오

### 공유 링크

- 만료일 설정 및 만료 후 접근 거부
- 비밀번호 보호 링크 — 정확한 비밀번호로만 접근
- 권한 상속 — 링크로 공유된 폴더의 하위 항목 접근 범위

### 멀티 디바이스 / 멀티 환경

- PC Web (`web.{env}-directcloud.jp`)
- Manager (`boxmanager.{env}-directcloud.jp`)
- Admin (`boxadmin.{env}-directcloud.jp`)

---

## 환경별 서버 URL

| 환경 | Admin | Manager | PCWeb |
|------|-------|---------|-------|
| **DEV** | `boxadmin.dev-directcloud.jp` | `boxmanager.dev-directcloud.jp` | `web.dev-directcloud.jp` |
| **TEST** | `tboxadmin.directcloud.jp` | `tboxmanager.directcloud.jp` | `tweb.directcloud.jp` |
| **QA** | `boxadmin.qa-directcloud.jp` | `boxmanager.qa-directcloud.jp` | `web.qa-directcloud.jp` |
| **STG** | `sboxadmin.directcloud.jp` | `sboxmanager.directcloud.jp` | `sweb.directcloud.jp` |

> 환경 URL은 `config/pages.json`의 `directcloud_environments` 키에서도 참조 가능.

---

## TC 작성 전략

### 테스트 피라미드

- E2E (Playwright): 핵심 사용자 흐름 — 로그인, 업로드, 다운로드, 공유, 삭제
- 역할별 분리: Admin TC / Manager TC / PCWeb TC 각각 별도 파일

### AAA 패턴 적용

```python
def test_upload_file_and_verify(page: Page):
    # Arrange — 로그인, 대상 폴더 진입
    login(page, COMPANY, USER_ID, PASSWORD)
    page.locator('#mybox').click()
    page.wait_for_url(re.compile(r'/mybox/'), timeout=10000)

    # Act — 파일 업로드 (API 방식)
    upload_via_api(page, 'test_file.txt', 'content')
    page.reload()

    # Assert — 파일 목록에 표시 확인
    file_row = page.locator('li:has(h6:has-text("test_file.txt"))').first
    expect(file_row).to_be_visible(timeout=15000)
```

### Edge Case 최소 3개 포함

- Empty state (빈 폴더/빈 리스트)
- 최대 길이 입력 (파일명, 폴더명)
- 특수문자 포함 입력

---

## Obsidian Vault 참조 가이드

| TC 주제 | 참조 경로 |
|---------|----------|
| 로그인, 권한 | `보안·관리/` |
| 파일 업로드·다운로드 | `파일 작업/` |
| My Box, Shared Box | `스토리지/` |
| Drive 기능 | `Drive/` |
| AI 기능 | `AI/` |
| Connect | `기타/` |

---

## CORS 규칙 (API 직접 호출 시)

| API | 경로 패턴 | CORS | 사용 가능 |
|-----|----------|------|----------|
| 내부 v1 | `api.qa-directcloud.jp/v1/*` | ❌ 차단 | 서버 사이드만 |
| 내부 v2 | `api.qa-directcloud.jp/v2/*` | ✅ 허용 | `page.evaluate()` OK |
| Uploader v1 | `uploader.qa-directcloud.jp/v1/*` | ✅ 허용 | `page.evaluate()` OK |

> **삭제 API**: 반드시 v2 통합 삭제 API (`POST /v2/item/delete`) + XHR 사용.
> `dirs` 파라미터에는 `folder.node` (인코딩 문자열), `files`에는 `file.file_seq` 사용.
> `dir_seq`를 `dirs`에 쓰면 무시됨.

---

## 커버리지 목표

| 영역 | 목표 |
|------|------|
| ACL 역할별 핵심 흐름 | 100% |
| 파일 CRUD (업로드·다운로드·삭제·이름변경) | 100% |
| 공유 링크 생성·만료 | 100% |
| UI 컴포넌트 (모달·드롭다운) | 70% 이상 |
