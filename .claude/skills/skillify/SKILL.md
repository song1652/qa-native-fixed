---
name: skillify
description: qa-native 세션에서 발견한 반복 패턴을 heal-patterns SKILL.md 또는 lessons_learned에 공식 등록
origin: qa-native
---

# Skillify (qa-native)

세션 중 발견한 반복 성공 패턴을 재사용 가능한 형태로 프로젝트에 등록하는 스킬.
매번 같은 패턴을 재발견하지 않도록 세션 끝에 호출.

## 언제 사용하나

- 힐링 패치가 N개 이상 파일에 동일하게 적용됐을 때
- 새로운 셀렉터·대기 전략이 효과가 있었을 때
- "이 패턴 다음에도 쓸 것 같다" 싶은 게 나왔을 때

## 등록 대상 결정

| 패턴 유형 | 등록 위치 |
|-----------|-----------|
| 오류 유형별 수정 전략 | `.claude/skills/heal-patterns/SKILL.md` |
| Playwright 셀렉터·대기 전략 | `.claude/skills/playwright-best-practices/SKILL.md` |
| 사이트별 특화 노하우 | `agents/lessons_learned.md` (사이트별 섹션) |
| 파이프라인 운영 패턴 | `CLAUDE.md` 또는 `doc/SCRIPTS_GUIDE.md` |

## 등록 워크플로우

1. **패턴 추출**: 이번 세션에서 반복된 수정 내용을 1-2줄로 요약
2. **중복 확인**: 이미 등록된 패턴인지 대상 파일에서 검색
3. **위치 결정**: 위 테이블 기준으로 어디에 넣을지 결정
4. **포맷 맞춰 기록**:
   - heal-patterns: `### N. 오류타입\n\`\`\`python\n# 패턴\n\`\`\``
   - lessons_learned: `- **키워드**: 설명 (대안 포함)`
5. **확인**: 등록 후 파일 읽어서 위치·포맷 검증

## heal-patterns 등록 포맷

```markdown
### N. 패턴명
```
Error: 에러 메시지 예시
```
```python
# Fix: 해결 방법
page.locator('...').do_something()
```

## lessons_learned 등록 포맷

```
- **키워드 (사이트명)**: 구체적 설명. 대안: `코드 예시`
```

## 규칙

- 단 1회만 효과 있었던 패턴은 등록하지 않는다 (최소 2회 이상)
- 이미 있는 항목은 업데이트하지 않고 그냥 넘어간다
- 등록 후 세션 종료 전 `lessons_learned.md` 마지막 섹션 확인
