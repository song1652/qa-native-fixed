# qa-native 작업 인수인계

> 새 Claude Code 세션에 이 파일을 첨부하거나 내용을 붙여넣고 시작하세요.
> "이 문서 읽고 이어서 병렬 파이프라인에도 headless 자동실행 추가해줘" 라고 말하면 바로 이어서 작업 가능합니다.

## 배경

`https://github.com/song1652/qa-native` — Playwright + Claude Code 기반 QA 자동화 프로젝트를 전체적으로 분석하고, 발견한 버그/설계 문제를 실제로 고친 뒤 실행까지 검증한 세션.

## 최종 결과물 (여기가 진실의 원천)

- **https://github.com/song1652/qa-native-fixed** ← 이번 수정사항 전부 반영된 완성본. `main` 브랜치가 최신 상태.
- 원본 `song1652/qa-native`은 건드리지 않음 (PR #1을 열었다가 별도 저장소로 반영 완료 후 닫음).

## 이번에 고친 것 (전부 `qa-native-fixed`의 커밋 메시지에도 상세 기록됨)

### 버그 수정
1. `.claude/settings.json` — UserPromptSubmit 훅 6개의 하드코딩 절대경로(`/Users/songkyoungjin/qa-native`) → `$CLAUDE_PROJECT_DIR`로 교체. 다른 컴퓨터에서 클론하면 훅이 전부 조용히 실패하던 문제.
2. `parallel/00_split.py` 삭제 — `run_qa_parallel.py`와 이원화된 죽은 병렬 아키텍처. 관련 문서(`doc/DIRECTORY.md`, `doc/SCRIPTS_GUIDE.md`, `scripts/update_directory.py`)도 정리.
3. `testcases/yafit_money/tc_99_demo_fail` — 의도적 실패 데모 TC에 `@pytest.mark.skip` 추가. 정규 회귀마다 힐링 루프 낭비하던 문제.
4. `agents/dashboard/serve.py` — `_post_import_convert`에 경로탈출 검증 누락 수정 (`scripts/_validators.py`로 검증 로직 분리, 실제 함수 단위 테스트로 교체).
5. `parallel/99_merge.py` — 타임아웃 로그 메시지(900초) vs 실제 값(7200초) 불일치 수정.
6. `scripts/_constants.py` — `prompts/plan_deliberation.md` 등이 전제하는 `step="planned"`가 `VALID_TRANSITIONS` FSM에 없어서 문서대로 하면 크래시하던 버그. FSM에 `"planned"` 상태 추가.
7. `requirements.txt` — `pytest-xdist`, `openpyxl` 누락 추가 (각각 `05_execute.py`의 `-n4 --dist=load`, 대시보드 엑셀 임포트에서 실제로 필요했는데 빠져있었음).
8. `config/pipeline.json`/`.gitignore` 등 자잘한 정리.

### 힐링 아키텍처 보강
- `parallel/99_merge.py`에 assertion 스냅샷 추적(`pre_heal_assertions`/`original_assertions`) 추가 — 원래 `06_heal.py`(단일 파이프라인)에만 있고, 실사용 비중이 더 큰 병렬 파이프라인엔 전혀 없어서 힐링 중 assertion 약화를 못 잡던 문제.
- `scripts/heal_utils.py`의 `compare_assertions()` — "정밀 assertion(`to_have_text`) → 느슨한 assertion(`to_be_visible`)으로 대체" 패턴 탐지 추가.
- `MAX_HEAL` 상수를 `_constants.py`로 중앙화.
- `scripts/06_auto_heal.py`의 사이트별 하드코딩 패처(`fix_ad_removal`) 제거.

### 기능 추가: 단일 파이프라인 headless 자동실행 (완료, 라이브 검증됨)
- `run_qa.py`가 이제 기본(`--auto`)으로 `claude -p`(headless) 세션을 자동으로 띄워서 `01_analyze → 코드작성 → lint → 승인 → 실행 → 힐링`까지 사람 개입 없이 완주시킵니다.
- `--no-auto`로 기존 방식(안내 메시지만 출력)으로 되돌릴 수 있음.
- 로컬 자동화용으로 `--dangerously-skip-permissions` 사용 (`.claude/settings.json`의 allow 리스트만으로는 workspace trust 문제로 무시됨 — 신뢰 안 하는 환경에선 재검토 필요).
- **실제로 the-internet.herokuapp.com/login(공개 QA 연습 사이트)을 대상으로 라이브 테스트해서 사람 개입 없이 `state=done`, 테스트 통과까지 완주 확인함.**

## 🔜 남은 작업: 병렬 파이프라인에도 headless 자동실행 추가

`run_qa_parallel.py`는 아직 옛날 방식 그대로임 — `PARALLEL_SUBAGENT_CONTEXTS`를 출력만 하고, 사람이나 인터랙티브 Claude 세션이 그걸 읽어서 Agent tool로 직접 실행해줘야 함.

**할 일**: `run_qa.py`에 만든 `_launch_headless_pipeline()` 패턴을 `run_qa_parallel.py`에도 적용.
- `run_qa_parallel.py`의 `main()` 마지막 부분(`PARALLEL_SUBAGENT_CONTEXTS_START/END` 출력하는 곳) 이후에, `claude -p`로 headless 세션을 띄워서 그 출력을 바탕으로 배치들을 Agent tool로 동시 실행하도록 지시하는 프롬프트를 넘기면 됨.
- `parallel/99_merge.py`도 이어서 자동으로 실행되게 하려면, headless 프롬프트에 "완료 후 `python parallel/99_merge.py`까지 실행해줘"를 포함시킬 것.
- 참고 구현: `qa-native-fixed` 저장소의 `run_qa.py`에 있는 `HEADLESS_PROMPT`, `_launch_headless_pipeline()` 함수.

## 재현/검증 환경 세팅 (참고)

```bash
git clone https://github.com/song1652/qa-native-fixed.git
cd qa-native-fixed
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
.venv/bin/python -m pytest tests/test_core_parsers.py -v   # 41개 통과해야 정상
```

라이브 파이프라인 테스트할 때 쓴 사이트: `https://the-internet.herokuapp.com/login` (공개 QA 연습용, 로그인 성공/실패 테스트하기 좋음. 테스트 계정: `tomsmith` / `SuperSecretPassword!` — 사이트 자체에 공개된 데모 계정).

## GitHub 인증 관련 참고

- `song1652` 계정 GitHub 인증은 `gh auth login --web` (device flow)로 진행했음. `gh`가 설치돼 있으면 `gh auth status`로 로그인 상태 확인 가능.
- 로그인 안 돼있으면 `gh auth login --web`으로 브라우저에서 다시 인증 필요 (이메일 2차 인증 코드가 `skj94268@gmail.com`으로 감).
