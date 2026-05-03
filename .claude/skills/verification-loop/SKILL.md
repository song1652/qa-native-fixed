---
name: verification-loop
description: Comprehensive verification system with 6-phase checklist. Run after completing a feature or before creating a PR.
origin: ECC
---

# Verification Loop

## When to Run

- 기능 구현 완료 후
- PR 생성 전
- 힐링 패치 적용 후
- 15분마다 (장시간 작업 시)

## 6단계 검증 체크리스트

### Phase 1: Build Verification
```bash
# Python 프로젝트
python -m py_compile scripts/*.py
python -m py_compile tests/generated/**/*.py

# 임포트 오류 확인
python -c "import scripts.heal_utils; print('OK')"
```

### Phase 2: Type Check
```bash
# mypy (설치된 경우)
mypy scripts/ --ignore-missing-imports

# 기본 문법 확인
python -m ast scripts/05_execute.py
```

### Phase 3: Lint Check
```bash
flake8 tests/generated/ --max-line-length=120 --ignore=E501,W503
flake8 scripts/ --max-line-length=120
```

### Phase 4: Test Suite (80% 커버리지 목표)
```bash
# 전체 실행
python scripts/05_execute.py --no-report

# 실패만 재실행
python scripts/05_execute.py --no-report --only-failed

# 커버리지 포함
pytest tests/ --cov=scripts --cov-report=term-missing
```

### Phase 5: Security Scan
```python
# 체크 항목
SECURITY_CHECKS = [
    "하드코딩된 비밀번호/API 키 없음",
    "print()에 민감 정보 노출 없음",
    "subprocess에 사용자 입력 직접 전달 없음",
    "eval()/exec() 사용 없음",
]
```

### Phase 6: Diff Review
```bash
git diff --stat
git diff -- scripts/ tests/generated/
```

## 검증 결과 판정

```
READY for PR:
  [v] Build    -- 컴파일 오류 없음
  [v] Types    -- 타입 오류 없음
  [v] Lint     -- flake8 통과
  [v] Tests    -- 전체 통과 (pass rate >= 80%)
  [v] Security -- 민감 정보 없음
  [v] Diff     -- 의도한 변경만 포함

NOT READY:
  [x] 실패 항목 목록
  --> 수정 필요 사항
```

## qa-native 힐링 루프 적용

```
패치 완료
  --> Phase 3 (Lint) 즉시 확인
  --> Phase 4 (Test) --only-failed 로 재실행
  --> 전체 통과 시 Phase 6 (Diff) 최종 검토
  --> READY 판정 후 리포트 생성
```

## 자동화 스크립트 예시

```python
def run_verification_loop(test_files: list[str]) -> dict:
    """패치 후 검증 루프 실행"""
    results = {}

    # Phase 3: Lint
    lint_result = subprocess.run(
        ["flake8"] + test_files + ["--max-line-length=120"],
        capture_output=True, text=True
    )
    results["lint"] = lint_result.returncode == 0

    # Phase 4: Test
    test_result = subprocess.run(
        [PYTHON_EXE, "scripts/05_execute.py", "--no-report", "--only-failed"],
        capture_output=True, text=True
    )
    results["tests"] = test_result.returncode == 0

    results["ready"] = all(results.values())
    return results
```
