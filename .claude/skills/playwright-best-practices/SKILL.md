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
> # DirectCloud: SPA 메뉴 전환 후 렌더링 대기 (networkidle 미발생)
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
