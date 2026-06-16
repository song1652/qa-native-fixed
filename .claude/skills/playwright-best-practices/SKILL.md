---
name: playwright-best-practices
description: Playwright Python 테스트 작성 베스트프랙티스. qa-native 프로젝트 전용 규칙 포함.
origin: qa-native
---

# Playwright Best Practices (qa-native)

## 필수 규칙

### 셀렉터 우선순위
1. `data-testid` 속성 (최우선)
2. `role` + `name` (`get_by_role`)
3. `placeholder` (`get_by_placeholder`)
4. CSS 클래스 (최후 수단)

```python
# Best
page.locator('[data-testid="login-btn"]').click()
page.get_by_role("button", name="로그인").click()

# Avoid
page.locator('.btn.btn-primary').click()
page.locator('button:nth-child(2)').click()
```

### 대기 전략

```python
# GOOD: 상태 기반 대기 (기본 원칙)
page.wait_for_load_state('networkidle')
page.locator('[data-testid="result"]').wait_for(state='visible')
expect(page.locator('.success')).to_be_visible()

# BAD: 시간 기반 대기 (원칙적으로 지양)
page.wait_for_timeout(3000)
import time; time.sleep(2)
```

> **예외 — SPA / 렌더링 지연 특수 케이스**: React 기반 SPA처럼 상태 변화 없이 UI만 갱신되는 경우,
> `wait_for_load_state` 로 감지 불가능한 전환 구간에서 짧은 `wait_for_timeout(300~2000)` 허용.
> 단, 사유를 주석으로 명시해야 함.
> ```python
> # SPA 메뉴 전환 후 렌더링 대기 (networkidle 미발생)
> page.wait_for_timeout(1500)
> ```

### Strict Mode 위반 방지

```python
# 여러 요소 매칭 시 -> .first 사용
page.locator('input[type="text"]').first.fill('값')

# 또는 더 구체적인 셀렉터
page.locator('form#login input[name="username"]').fill('값')
```

### 페이지 이동 패턴

```python
def goto_and_wait(page, url: str):
    page.goto(url)
    page.wait_for_load_state('networkidle')
    # 광고/팝업 제거
    page.evaluate("""
        document.querySelectorAll(
            'ins.adsbygoogle, iframe[src*=google], .popup, [class*=cookie-banner]'
        ).forEach(e => e.remove())
    """)
```

### Assertions

```python
from playwright.sync_api import expect

# 가시성
expect(locator).to_be_visible()
expect(locator).to_be_hidden()

# 텍스트
expect(locator).to_contain_text("텍스트")
expect(locator).to_have_text("정확한 텍스트")

# URL / 타이틀
expect(page).to_have_url("https://...")
expect(page).to_have_title("페이지 타이틀")

# 입력값
expect(locator).to_have_value("입력값")

# 활성/비활성
expect(locator).to_be_enabled()
expect(locator).to_be_disabled()
```

## 테스트 파일 필수 구조

```python
"""
tc_{번호}_{english_snake_case}.py
- BASE_URL, import, 상수를 이 파일에 직접 포함 (공유 헬퍼 금지)
- 테스트 함수명: test_{english_snake_case}
"""
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "https://example.com"  # 또는 config에서 로드


def test_english_snake_case(page: Page):
    """테스트 설명"""
    page.goto(f"{BASE_URL}/path")
    page.wait_for_load_state('networkidle')

    # 액션
    page.locator('[data-testid="element"]').click()

    # 검증
    expect(page.locator('[data-testid="result"]')).to_be_visible()

    # 스크린샷 (실패 시 증거)
    page.screenshot(path="tests/screenshots/test_english_snake_case.png")
```

## 스크린샷 규칙

- 경로: `tests/screenshots/{test_name}.png`
- 시점: assert 직전 또는 실패 시
- `--no-report` 모드: 힐링 중 스크린샷 최소화

---

## React 16 SPA 이벤트 처리

React 16 기반 SPA 앱은 이벤트를 `document` 레벨에서 위임하므로
`locator.click()`이 React 이벤트 핸들러를 미트리거하는 경우가 있다.

### Toolbar 버튼 — `page.mouse.click(좌표)` 필수

```python
# ✅ 좌표 기반 real browser event
coords = page.evaluate("""() => {
    const btn = document.querySelector('button[data-name="새 폴더"]')
             || document.querySelector('button[data-name="新規フォルダ"]');
    if (!btn) return null;
    const rect = btn.getBoundingClientRect();
    return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
}""")
if coords:
    page.mouse.click(coords['x'], coords['y'])

# ❌ React 핸들러 미트리거
page.locator('button[data-name="새 폴더"]').click()

# ❌ isTrusted=false — React 무시
page.evaluate("document.querySelector('button').dispatchEvent(new MouseEvent('click'))")
```

**적용 대상**: 파일 목록 toolbar 버튼 (새 폴더, 업로드, 삭제, 다운로드 등)

### Bootstrap 모달 내 버튼 — `locator.click()` 사용

```python
# ✅ Bootstrap 모달 내부 — 네이티브 Playwright click (좌표 기반 불안정)
modal = page.locator('#modal-new-folder')
submit_btn = modal.locator(
    'button[type="submit"], button:has-text("생성"), button:has-text("作成"), button:has-text("Create")'
).first
submit_btn.click()
```

### Click 방식 결정 기준

| 대상 | 방식 | 이유 |
|------|------|------|
| React SPA toolbar 버튼 | `page.mouse.click(좌표)` | React 16 이벤트 위임 |
| Bootstrap 모달 내 버튼 | `locator.click()` | Bootstrap 직접 바인딩 |
| 로그인 폼 submit | `locator.click()` | 일반 form submit |
| 좌측 사이드바 | `locator.click()` | 직접 DOM 이벤트 |
| 컨텍스트 메뉴 항목 | `locator.click()` | jQuery contextMenu |

---

## Tip 팝업 처리 (SPA 앱 필수)

React SPA 앱 최초 방문 시 styled-components 기반 Tip 팝업이 z-index 999로 표시된다.
**Bootstrap `.popover`가 아니다.**

```python
def dismiss_tip_popup(page):
    """z-index 기반 DOM 탐색 후 좌표 클릭으로 팝업 닫기"""
    page.wait_for_timeout(2000)  # SPA 렌더링 후 팝업 지연 표시
    result = page.evaluate("""() => {
        const els = Array.from(document.querySelectorAll('*'));
        for (const el of els) {
            const style = window.getComputedStyle(el);
            const zi = parseInt(style.zIndex || '0');
            if (zi > 100 && (style.position === 'fixed' || style.position === 'absolute')) {
                const text = el.innerText || '';
                if (text.includes('Tip') || text.includes('팁') || text.includes('ヒント')) {
                    const rect = el.getBoundingClientRect();
                    return { x: rect.right - 20, y: rect.top + 20 };
                }
            }
        }
        return null;
    }""")
    if result:
        page.mouse.click(result['x'], result['y'])
        page.wait_for_timeout(300)

# ❌ React 앱 파괴
# page.evaluate("document.querySelector('.tip-popup').remove()")

# ❌ styled-components는 .popover가 아님
# page.locator('.popover .close').click()
```

**사용 시점**: beforeEach, toolbar 버튼 클릭 전에도 재호출 (팝업이 버튼을 가릴 수 있음)

---

## 파일 업로드 패턴

headless Chromium에서는 `set_input_files` / `filechooser` 이벤트가 불안정하다.

```python
# ❌ headless에서 불안정
# with page.expect_file_chooser() as fc_info:
#     page.click('#upload-button')
# fc_info.value.set_files('path/to/file')

# ✅ API 직접 호출 (안정적)
# 1. access_token 쿠키 추출
# 2. React Fiber에서 currentDirSeq (현재 디렉토리 ID) 추출
# 3. POST https://your-app.example.com/v1/files 호출
# 4. page.reload() + dismiss_tip_popup() 으로 파일 목록 갱신
```

---

## 셀렉터 규칙

```python
import re

# ✅ 고유 ID 기반
page.locator('#mybox')
page.locator('#sharedbox')
page.locator('#trash')
page.locator('#modal-new-folder')

# ✅ data 속성 기반
page.locator('button[data-name="새 폴더"]')
page.locator('[data-action="delete"]')

# ✅ 파일/폴더 행 (h6 구조 + fallback)
page.locator(f'li:has(h6:has-text("{name}")), [data-name="{name}"]').first

# ✅ 다국어 — 반드시 re.compile 사용
# 쉼표 구분 'text=A, text=B' 는 Playwright에서 OR가 아니라 리터럴로 해석됨!
page.get_by_role("button", name=re.compile(r"生成|생성|Create"))
page.get_by_role("button", name=re.compile(r"ログアウト|로그아웃|Logout"))
page.locator('li.contextmenu-item').filter(has_text=re.compile(r"削除|삭제|Delete")).first

# ❌ 추측 기반 금지
# page.locator('[class*="header"]')
# page.locator('.sc-ccLTTT')  # styled-components 동적 클래스
# page.locator('text=ログアウト, text=로그아웃')  # 쉼표는 OR가 아님!
```

---

## 타이밍 & 대기 전략

### 타임아웃 계층

| 레벨 | 시간 | 용도 |
|------|------|------|
| 네트워크/네비게이션 | 30s | `wait_for_load_state('networkidle')` |
| 요소 가시성 대기 | 10-15s | `locator.wait_for(state='visible', timeout=15000)` |
| 모달/다이얼로그 | 10-20s | `modal.wait_for(state='visible', timeout=20000)` |
| SPA 렌더링 대기 | 1500-3000ms | toolbar 클릭 전, Tip 팝업 제거 전 |
| 애니메이션 | 300-500ms | `wait_for_timeout(300)` |

> **중요**: `is_visible(timeout=N)` — timeout 파라미터가 **무시**된다.
> 대기가 필요하면 반드시 `wait_for(state='visible', timeout=N)` 또는
> `expect(locator).to_be_visible(timeout=N)` 사용.

```python
# ✅ 삭제 후 안정적 확인
page.wait_for_load_state('networkidle')
target_row.wait_for(state='hidden', timeout=15000)
assert not target_row.is_visible()

# ✅ SPA 로그인 후 URL 검증 (다양한 랜딩 패턴 모두 허용)
page.wait_for_url(re.compile(r'/(mypage|home|top|files|drive)'), timeout=30000)

# ✅ SPA 진입 후 필수 대기 순서
page.locator('#mybox').click()
page.wait_for_url(re.compile(r'/mybox/'), timeout=20000)
page.wait_for_load_state('networkidle')
page.wait_for_timeout(2000)
dismiss_tip_popup(page)

# ✅ domcontentloaded 금지 — React SPA 렌더링 전 발생
# page.wait_for_load_state('domcontentloaded')  # BAD: 요소 아직 없음
page.wait_for_load_state('networkidle')  # GOOD
```

---

## 재시도 패턴

```python
# 모달 열기 재시도 (최대 5회)
modal = page.locator('#modal-new-folder')
for attempt in range(5):
    dismiss_tip_popup(page)
    coords = page.evaluate("""() => {
        const btn = document.querySelector('button[data-name="새 폴더"]');
        if (!btn) return null;
        const rect = btn.getBoundingClientRect();
        return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
    }""")
    if coords:
        page.mouse.click(coords['x'], coords['y'])
    try:
        modal.wait_for(state='visible', timeout=3000)
        break
    except Exception:
        page.wait_for_timeout(500)
modal.wait_for(state='visible', timeout=10000)

# 조건부 존재 확인 (이미 존재하면 스킵)
try:
    existing.wait_for(state='visible', timeout=2000)
    return  # 이미 존재 — 생성 스킵
except Exception:
    pass
```

---

## 클린업 패턴

```python
import pytest

QA_PREFIX = "[QA_TEST]"

@pytest.fixture(autouse=True)
def cleanup(page):
    yield
    # 모든 클린업은 try/except로 감싸고 실패 무시
    try:
        cleanup_test_folder(page, f"{QA_PREFIX}_folder_test")
    except Exception:
        pass
```

---

## 로그아웃 테스트 — 3단계 전략 (60초 제한)

SPA 로그아웃은 환경·플랜별 UI가 달라 단일 전략으로 신뢰할 수 없다. 각 전략의 timeout을 짧게 설정한다.

```python
import re

page.on('dialog', lambda d: d.accept())  # 네이티브 confirm 대응
logout_clicked = False

# 전략 1: 직접 로그아웃 링크 (2초)
direct_logout = page.locator('a[href*="logout"], a[href*="signout"]').first
if direct_logout.is_visible():
    direct_logout.click()
    logout_clicked = True

# 전략 2: 프로필 → 설정 → 로그아웃 (최대 2회, ~15초)
if not logout_clicked:
    for attempt in range(2):
        dismiss_tip_popup(page)
        page.locator('h3').first.click()
        try:
            settings_heading.wait_for(state='visible', timeout=3000)
        except Exception:
            continue
        logout_btn = page.locator('button, a').filter(
            has_text=re.compile(r'ログアウト|로그아웃|Logout', re.IGNORECASE)
        ).first
        if logout_btn.is_visible():
            logout_btn.click()
            logout_clicked = True
            break

# 전략 3: URL 직접 이동 (최후 수단, 거의 항상 성공)
if not logout_clicked:
    from urllib.parse import urlparse
    base_url = f"{urlparse(page.url).scheme}://{urlparse(page.url).netloc}"
    page.goto(f"{base_url}/auth/logout")

# URL 미변경 시 쿠키 삭제 fallback
page.context.clear_cookies()
page.reload()
page.wait_for_load_state('networkidle')
on_login_page = '/login' in page.url
has_login_form = page.locator('input[name="id"]').first.is_visible()
assert on_login_page or has_login_form
```
