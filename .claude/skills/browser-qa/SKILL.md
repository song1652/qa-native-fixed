---
name: browser-qa
description: Automated visual testing and UI interaction verification using browser automation after deploying features.
origin: ECC
---

# Browser QA -- Automated Visual Testing & Interaction

## Overview

Deploy this skill after staging/preview releases, during PR reviews touching frontend code, and before production shipping to confirm layouts and interactions function correctly.

Compatible with: claude-in-chrome (preferred), Playwright MCP, Puppeteer

## 4단계 테스트 플로우

### Phase 1: Smoke Test (배포 상태 확인)
- 콘솔 에러 없음 확인
- 네트워크 실패 없음 확인
- Core Web Vitals 성능 메트릭 확인
- 페이지 기본 렌더링 확인

### Phase 2: Interaction Test (기능 동작 검증)
- 네비게이션 링크 동작
- 폼 제출 (유효/무효 상태)
- 인증 플로우 (로그인/로그아웃)
- 핵심 사용자 여정(Critical User Journey)

### Phase 3: Visual Regression (시각적 회귀)
- 3개 반응형 브레이크포인트 스크린샷
  - Desktop: 1280px
  - Tablet: 768px
  - Mobile: 375px
- 레이아웃 이슈 탐지 (5px 이상 이동, 요소 누락)

### Phase 4: Accessibility (접근성)
- WCAG AA 위반 체크
- 키보드 내비게이션 검증
- 스크린 리더 지원 확인

## Playwright Python 패턴

```python
from playwright.sync_api import Page, expect

def smoke_test(page: Page, url: str):
    """배포 후 기본 동작 확인"""
    errors = []
    page.on("console", lambda msg: errors.append(msg) if msg.type == "error" else None)

    page.goto(url)
    page.wait_for_load_state('networkidle')

    assert len(errors) == 0, f"콘솔 에러 발생: {errors}"
    assert page.title() != "", "페이지 타이틀 없음"

def visual_snapshot(page: Page, name: str):
    """반응형 브레이크포인트별 스크린샷"""
    breakpoints = [
        ("desktop", 1280, 800),
        ("tablet", 768, 1024),
        ("mobile", 375, 812),
    ]
    for label, width, height in breakpoints:
        page.set_viewport_size({"width": width, "height": height})
        page.wait_for_load_state('networkidle')
        page.screenshot(path=f"tests/screenshots/{name}_{label}.png", full_page=True)

def interaction_test(page: Page, url: str):
    """주요 인터랙션 검증"""
    page.goto(url)
    page.wait_for_load_state('networkidle')

    # 광고/팝업 제거
    page.evaluate("""
        document.querySelectorAll('ins.adsbygoogle, .popup, .modal-overlay')
            .forEach(e => e.remove())
    """)

    # 폼 요소 확인
    forms = page.locator('form').all()
    for form in forms:
        expect(form).to_be_visible()
```

## 결과 판정 기준

| 판정 | 조건 |
|------|------|
| **SHIP** | 모든 단계 통과, 이슈 없음 |
| **SHIP WITH FIXES** | 마이너 이슈 있으나 블로커 아님 |
| **HOLD** | 크리티컬 버그 또는 접근성 위반 |

## qa-native 연동 포인트

- `01_analyze.py` DOM 분석 후 시각 검증에 활용
- 힐링 루프에서 패치 후 `browser-qa` Phase 1~2 실행으로 회귀 확인
- `tests/screenshots/` 에 결과 저장
