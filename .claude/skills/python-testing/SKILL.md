---
name: python-testing
description: Python testing strategies using pytest, TDD methodology, fixtures, mocking, parametrization, and coverage requirements.
origin: ECC
---

# Python Testing Patterns

## When to Activate

- 새 테스트 코드 작성 시 (TDD: red -> green -> refactor)
- pytest 픽스처/파라미터화 설계 시
- 테스트 커버리지 리뷰 시

## TDD Cycle

```
RED   -> 실패하는 테스트 먼저 작성
GREEN -> 테스트 통과하는 최소 코드 작성
REFACTOR -> 코드 개선 (테스트는 계속 통과)
```

**커버리지 목표: 80%+ (크리티컬 경로 100%)**

## pytest 핵심 패턴

### 기본 구조 (qa-native 스타일)

```python
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "https://example.com"

def test_login_success(page: Page):
    """로그인 성공 시 대시보드로 이동"""
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state('networkidle')

    page.locator('[data-testid="username"]').fill("admin")
    page.locator('[data-testid="password"]').fill("password")
    page.locator('[data-testid="submit"]').click()

    expect(page).to_have_url(f"{BASE_URL}/dashboard")
```

### Fixtures

```python
import pytest

@pytest.fixture
def logged_in_page(page):
    """로그인 상태 픽스처"""
    page.goto(f"{BASE_URL}/login")
    page.locator('[name="username"]').fill("admin")
    page.locator('[name="password"]').fill("password")
    page.locator('[type="submit"]').click()
    page.wait_for_load_state('networkidle')
    yield page

def test_dashboard_visible(logged_in_page):
    """로그인 후 대시보드 확인"""
    expect(logged_in_page.locator('.dashboard')).to_be_visible()
```

### Parametrize

```python
@pytest.mark.parametrize("username,password,expected_error", [
    ("", "password", "아이디를 입력하세요"),
    ("admin", "", "비밀번호를 입력하세요"),
    ("wrong", "wrong", "로그인 정보가 올바르지 않습니다"),
])
def test_login_errors(page, username, password, expected_error):
    """다양한 오류 케이스 파라미터화"""
    page.goto(f"{BASE_URL}/login")
    page.locator('[name="username"]').fill(username)
    page.locator('[name="password"]').fill(password)
    page.locator('[type="submit"]').click()

    expect(page.locator('.error-message')).to_contain_text(expected_error)
```

### Mocking

```python
from unittest.mock import patch, Mock

@patch("scripts.heal_utils.classify_error")
def test_heal_classify(mock_classify):
    mock_classify.return_value = "strict_mode"

    result = mock_classify("strict mode violation")

    mock_classify.assert_called_once()
    assert result == "strict_mode"
```

## Assertions 빠른 참조

```python
# Playwright assertions
expect(locator).to_be_visible()
expect(locator).to_be_hidden()
expect(locator).to_contain_text("텍스트")
expect(locator).to_have_value("값")
expect(page).to_have_url("https://...")
expect(page).to_have_title("제목")

# pytest assertions
assert result == expected
assert result is not None
assert "text" in response
with pytest.raises(ValueError, match="invalid"):
    raise ValueError("invalid input")
```

## Markers (pytest.ini 등록)

```ini
[pytest]
markers =
    slow: 느린 테스트 (네트워크, 파일 IO)
    integration: 외부 서비스 연동 테스트
    smoke: 기본 동작 확인 (빠른 실행)
    healing: 힐링 후 재실행 대상
```

```bash
# 빠른 테스트만
pytest -m "not slow"

# 스모크 테스트
pytest -m smoke

# 마지막 실패만
pytest --lf
```

## conftest.py 패턴

```python
# tests/conftest.py
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "locale": "ko-KR",
    }

@pytest.fixture(autouse=True)
def cleanup_screenshots(request):
    yield
    # 테스트 통과 시 스크린샷 삭제
    if request.node.rep_call.passed:
        screenshot = Path(f"tests/screenshots/{request.node.name}.png")
        if screenshot.exists():
            screenshot.unlink()
```

## Do / Don't

### DO
- 테스트 함수명: `test_{english_snake_case}` (영문 필수)
- 각 테스트 파일 자체 완결 (BASE_URL, import 직접 포함)
- `wait_for_load_state('networkidle')` 후 상호작용
- 파라미터화로 유사 케이스 묶기

### DON'T
- `time.sleep()` / `page.wait_for_timeout()` 절대 금지
- 공유 헬퍼 파일 생성 금지 (각 파일 자체 완결)
- 외부 LLM SDK import 금지
- 하드코딩된 URL/자격증명 금지 (test_data.json 사용)
