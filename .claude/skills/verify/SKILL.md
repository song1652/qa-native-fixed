---
name: verify
description: qa-native 패치 후 실제 통과 여부를 증거로 확인. 05_execute 기반 검증 플로우.
origin: qa-native
---

# Verify (qa-native)

힐링 패치·코드 수정 후 "정말 고쳐졌나?" 를 증거로 확인하는 스킬.
"됐을 것 같다"는 금지 — 실행 결과만 증거로 인정.

## 검증 순서

### 1단계 — 실패 테스트만 재실행 (기본)
```bash
python scripts/05_execute.py --no-report --only-failed
```
- 빠름. 패치한 파일만 재확인할 때 사용.

### 2단계 — 전체 재실행 (패스율 변화 확인)
```bash
python scripts/05_execute.py --no-report
```
- 패치 범위가 넓거나 공통 로직 수정 시 사용.

### 3단계 — 리포트 생성 (최종 통과 확인 후에만)
```bash
python scripts/05_execute.py
```
- 전체 통과 확인 후 마지막 1회만 실행.

## 검증 판정 기준

| 결과 | 판정 | 다음 액션 |
|------|------|-----------|
| 모든 failed 케이스 pass | ✅ 완료 | lessons_learned 기록 후 종료 |
| 일부 여전히 fail | 🔄 재힐링 | 동일 오류 2회 반복이면 스킵 |
| 새로운 fail 발생 | ⚠️ 회귀 | 패치 범위 재검토 |

## 리포트 해석

실행 후 출력에서 확인:
```
PASSED: N  FAILED: N  ERROR: N
```
- `state/pipeline.json` → `passed` / `failed` / `heal_count` 누적값 확인
- 스크린샷: `tests/screenshots/` (실패 시 자동 저장)

## 규칙

- 검증 없이 "완료"를 보고하지 않는다
- `--no-report` 옵션 없이 힐링 중 리포트 생성 금지
- 실패 로그가 있으면 숨기지 말고 그대로 보고
