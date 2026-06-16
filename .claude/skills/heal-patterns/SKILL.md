---
name: heal-patterns
description: qa-native 힐링 루프 패치 전략. 오류 유형별 수정 패턴과 lessons_learned 기록 규칙.
origin: qa-native
---

# Heal Patterns (qa-native)

## Sequential Thinking 활용 (힐링 1회차부터 필수)

힐링 진입 즉시, 오류 유형과 관계없이 `mcp__sequential-thinking__sequentialthinking` 도구를 호출해 단계적으로 분석한다.

**분석 흐름**:
1. 오류 메시지 + 스택 트레이스 → 가설 수립
2. 관련 DOM/셀렉터 확인 (MCP Playwright 또는 dom_info 참조)
3. 가설 검증 → 가장 유력한 원인 선택
4. 패치 전략 결정 (아래 오류 유형별 패턴 참조)
5. 패치 적용 → `05_execute.py --no-report --only-failed` 재실행

---

## 힐링 완료 체크리스트

1. [ ] 코드 패치 완료
2. [ ] `agents/lessons_learned.md` 교훈 기록 (중복 시 생략)
3. [ ] `05_execute.py --no-report --only-failed` 재실행 통과 확인

## 오류 유형별 패치 전략

### 1. Strict Mode Violation
```
Error: strict mode violation: locator('input') resolved to N elements
```
```python
# Fix A: .first 추가
page.locator('input').first.fill('값')

# Fix B: 더 구체적인 셀렉터
page.locator('input[name="username"]').fill('값')
page.locator('form#login >> input').first.fill('값')
```

### 2. Timeout / Element Not Found
```
Error: Timeout waiting for selector / Element not visible
```
```python
# Fix: networkidle 대기 추가
page.goto(url)
page.wait_for_load_state('networkidle')
page.locator('[data-testid="btn"]').wait_for(state='visible')
page.locator('[data-testid="btn"]').click()
```

### 3. Navigation / URL Mismatch
```
Error: expect(page).to_have_url() failed
```
```python
# Fix: 리다이렉트 대기
page.click('[type="submit"]')
page.wait_for_load_state('networkidle')
expect(page).to_have_url(re.compile(r'/dashboard'))
```

### 4. to_have_class 정규식
```
Error: to_have_class() string argument
```
```python
import re
# Fix: 문자열 -> re.compile()
expect(locator).to_have_class(re.compile(r'active'))
```

### 5. page.evaluate 문법 오류
```
Error: page.evaluate() - return statement
```
```python
# Bad
page.evaluate("return document.title")

# Fix: 화살표 함수 형식
page.evaluate("() => document.title")
```

### 6. 광고/팝업 오버레이 방해
```
Error: Element is covered by another element
```
```python
# Fix: goto 직후 광고 제거
page.goto(url)
page.wait_for_load_state('networkidle')
page.evaluate("""
    document.querySelectorAll(
        'ins.adsbygoogle, iframe[src*=google], iframe[src*=doubleclick],
         .popup, .modal, [class*=cookie], [id*=cookie]'
    ).forEach(e => e.remove())
""")
```

### 7. Import 오류
```
Error: ModuleNotFoundError / ImportError
```
```python
# Fix: 각 파일에 직접 import (공유 헬퍼 참조 금지)
import re
import json
from pathlib import Path
from playwright.sync_api import Page, expect
```

### 8. 인코딩 오류 (Windows cp949)
```
Error: UnicodeEncodeError 'cp949'
```
```python
# Fix A: 특수문자 제거 (em dash -> --)
'힐링 중 -- 최종 실행 시 생성'

# Fix B: _paths.py import (자동 UTF-8 설정됨)
from _paths import PROJECT_ROOT
```

## 반복 오류 스킵 규칙

동일 오류가 2회 연속 반복되면:
1. 해당 테스트 스킵 처리
2. `agents/lessons_learned.md`에 "미해결 패턴"으로 기록
3. 수동 수정 요청

## lessons_learned.md 기록 형식

```markdown
## [날짜] 패턴명
- **오류**: `오류 메시지 또는 유형`
- **원인**: 왜 발생했는지
- **수정**: 어떻게 고쳤는지 (코드 예시 포함)
- **재발 방지**: 코드 생성 시 주의사항
```

## 힐링 재실행 명령

```bash
# 실패 테스트만 재실행 (빠름)
python scripts/05_execute.py --no-report --only-failed

# 전체 재실행
python scripts/05_execute.py --no-report

# 자동 패치 먼저 시도
python scripts/06_auto_heal.py

# 힐링 컨텍스트 생성
python scripts/06_heal.py
```

---

## SPA/React 앱 힐링 패턴

### 9. Vue/React input 입력 실패 (nativeInputValueSetter)

Vue/React 앱에서 `locator.fill()`이 프레임워크 상태에 반영되지 않을 때:

```python
# ❌ fill()이 Vue/React 상태에 반영 안 됨
page.locator('[name="company_code"]').fill('회사코드')

# ✅ nativeInputValueSetter 패턴 (placeholder 순서 기준)
page.evaluate("""(args) => {
    const setter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
    ).set;
    const fields = Array.from(document.querySelectorAll('input'))
                        .filter(i => i.placeholder);
    setter.call(fields[0], args[0]);
    fields[0].dispatchEvent(new Event('input', {bubbles: true}));
    setter.call(fields[1], args[1]);
    fields[1].dispatchEvent(new Event('input', {bubbles: true}));
    setter.call(fields[2], args[2]);
    fields[2].dispatchEvent(new Event('input', {bubbles: true}));
}""", [company_code, user_id, password])
```

**적용 조건**: `fill()` 후 로그인 버튼 클릭해도 입력값이 비어있다는 에러 발생 시

### 10. React SPA toolbar 클릭 무반응

React 16 기반 SPA에서 `locator.click()`이 이벤트 핸들러를 트리거하지 않을 때:

```python
# ❌ React 핸들러 미트리거
page.locator('button[data-name="새 폴더"]').click()

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
```

### 11. Timeout 직후 요소 없음 — Tip 팝업 가림

toolbar 버튼 클릭이 timeout으로 실패하고 스크린샷에 팝업이 보일 때:

```python
# Tip 팝업이 버튼을 가리는 경우
page.wait_for_timeout(2000)
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
```

### 12. 삭제 확인 실패 — waitFor hidden 누락

삭제 후 `assert not row.is_visible()`이 flaky하게 실패할 때:

```python
# BAD — SPA 리렌더링 전 확인
assert not row.is_visible()

# GOOD — DOM 제거까지 대기
page.wait_for_load_state('networkidle')
try:
    row.wait_for(state='hidden', timeout=15000)
except Exception:
    pass
assert not row.is_visible()
```
