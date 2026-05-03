---
name: continuous-learning-v2
description: Instinct-based learning system with confidence scoring that evolves into skills/commands/agents. Project-scoped to prevent cross-project contamination.
origin: ECC
---

# Continuous Learning v2.1 -- Instinct-Based Architecture

## 개요

Claude Code 세션에서 재사용 가능한 지식을 "instinct"로 추출하는 시스템.
신뢰도 스코어링(0.3~0.9)으로 패턴을 관리하며, 프로젝트 범위 격리로 오염 방지.

## qa-native 연동: lessons_learned.md 업그레이드

기존 `agents/lessons_learned.md`를 이 패턴으로 강화:

### Instinct 구조

```yaml
instinct:
  id: "playwright_strict_mode_001"
  trigger: "strict mode violation / 여러 요소 매칭"
  action: "locator에 .first 추가 또는 더 구체적인 셀렉터 사용"
  confidence: 0.85
  domain: "e2e-testing"
  scope: "project"           # project | global
  evidence_count: 12         # 관찰된 횟수
  last_seen: "2026-04-08"
  fix_example: |
    # Before
    page.locator('input').fill('text')
    # After
    page.locator('input').first.fill('text')
```

### 신뢰도 진화 규칙

| 이벤트 | 신뢰도 변화 |
|--------|------------|
| 동일 패턴 재관찰 | +0.05 |
| 사용자 수동 기록 | +0.10 |
| 반례 발견 | -0.15 |
| 다른 프로젝트에서도 등장 | +0.10 |

### 자동 승격 조건

- 2개 이상 프로젝트에서 등장
- 평균 신뢰도 >= 0.80
- `project` -> `global` 자동 승격

## 도메인 태그 (qa-native 기준)

| 태그 | 설명 |
|------|------|
| `e2e-testing` | Playwright 테스트 패턴 |
| `selector` | DOM 셀렉터 전략 |
| `healing` | 힐링 루프 패턴 |
| `lint` | Flake8 수정 패턴 |
| `async` | 비동기 대기 패턴 |
| `encoding` | 인코딩/한글 처리 |

## 현재 qa-native 고신뢰도 Instincts

```yaml
- id: strict_mode_first
  confidence: 0.90
  trigger: "strict mode violation"
  action: ".first 추가"

- id: networkidle_wait
  confidence: 0.88
  trigger: "페이지 이동 후 요소 미검출"
  action: "wait_for_load_state('networkidle') 추가"

- id: utf8_stdout
  confidence: 0.95
  trigger: "Windows cp949 인코딩 오류"
  action: "sys.stdout UTF-8 래핑 또는 특수문자 제거"

- id: venv_scripts_path
  confidence: 0.92
  trigger: "Windows .venv/bin 없음"
  action: ".venv/Scripts/python.exe 경로 사용"
```

## 커맨드

| 커맨드 | 동작 |
|--------|------|
| `/instinct-status` | 학습된 instinct 목록 + 신뢰도 표시 |
| `/evolve` | 관련 instinct 클러스터링 -> 스킬/커맨드로 변환 |
| `/promote` | 프로젝트 instinct -> 글로벌 승격 |

## lessons_learned.md 기록 가이드

힐링/패치 시 즉시 기록:
```markdown
## [날짜] 패턴명
- **트리거**: 어떤 오류에서 발생
- **수정**: 어떻게 고쳤는지
- **신뢰도**: 0.0~1.0
- **재발 횟수**: N회
```
