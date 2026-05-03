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
