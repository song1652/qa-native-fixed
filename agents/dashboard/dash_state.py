"""dash_state.py — 상태 빌더·리스터 (serve.py Phase-2 분리).

serve.py의 DashboardHandler가 직접 import해서 사용하는 순수 함수 모음.
파일시스템을 읽어 응답 dict를 반환하거나 상태 파일을 갱신한다.
serve는 이 모듈을 import하고, 이 모듈은 serve를 import하지 않는다 (순환 import 방지).
"""
from __future__ import annotations

import json
import re
import stat
from datetime import datetime
from pathlib import Path

from _paths import (
    PROJECT_ROOT,
    PIPELINE_STATE as STATE_PATH,
    PARALLEL_STATE as PARALLEL_STATE_PATH,
    DISCUSS_STATE as DISCUSS_PATH,
    GENERATED_DIR,
    REPORTS_DIR,
    PAGES_JSON,
    TESTCASES_DIR,
    DIALOG_PATH,
    TEAM_NOTES_PATH,
    PENDING_IMPL_PATH,
)
from _pipeline_registry import (
    Step, ParallelStatus, PIPELINE_STEP_DEFS,
    STEP_COMPAT, PARALLEL_STEP_LABELS,
    STEP_DEF_BY_NAME,
)
from _validators import is_safe_filename


TEAM_NOTES_HEADER = (
    "# 팀 결정 사항\n\n"
    "> **독자**: 심의 Agent — 팀 토론 결론 누적. 토론 시 중복 결론 방지 목적으로 참조.\n\n"
    "---\n"
)


def load_json(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[Dashboard] JSON 파싱 실패: {path} — {e}")
            return None
    return None


def parse_conclusion_items(conclusion: str) -> list:
    """결론 마크다운을 투표 가능한 개별 항목으로 파싱."""
    items = []

    # 1) ### 소제목 파싱
    for m in re.finditer(r'^###\s+(.+?)\n([\s\S]*?)(?=^###\s|\Z)', conclusion, re.MULTILINE):
        title = m.group(1).strip()
        body  = re.sub(r'\n?---+\s*$', '', m.group(2)).strip()
        items.append({"id": len(items), "title": title, "text": body, "status": "pending"})

    # 2) 번호 목록 파싱 (1. **title**: body)
    if not items:
        for m in re.finditer(r'^\d+\.\s+(.+)$', conclusion, re.MULTILINE):
            text = m.group(1).strip()
            bold = re.match(r'\*\*(.+?)\*\*[:\s]*(.*)', text)
            title = bold.group(1).strip() if bold else text[:70]
            items.append({"id": len(items), "title": title, "text": text, "status": "pending"})

    # 3) 괄호 번호 패턴 파싱: (1) ... (2) ... 또는 인라인 구분
    if not items:
        parts = re.split(r'\s*\((\d+)\)\s*', conclusion)
        # parts: ['앞부분', '1', '내용1', '2', '내용2', ...]
        if len(parts) >= 3:
            for i in range(1, len(parts) - 1, 2):
                text = parts[i + 1].strip().rstrip('.')
                if not text:
                    continue
                # 첫 문장이나 키워드를 제목으로 추출
                title_match = re.match(r'^(.+?)[.:\-—]', text)
                title = title_match.group(1).strip() if title_match else text[:70]
                items.append({"id": len(items), "title": title, "text": text, "status": "pending"})

    # 4) fallback
    if not items:
        items.append({"id": 0, "title": "전체 결론", "text": conclusion, "status": "pending"})

    return items


def finalize_team_notes(discuss: dict):
    """승인된 항목만 team_notes.md에 덮어쓰기 + pending_impl.json 생성."""
    import datetime as _dt
    items = discuss.get("conclusion_items", [])
    approved = [i for i in items if i["status"] == "approved"]
    topic = discuss.get("topic", "")
    today = _dt.datetime.now().strftime("%Y-%m-%d")

    content = TEAM_NOTES_HEADER
    if approved:
        content += f"\n## {topic}\n> 결정일: {today}\n\n"
        for item in approved:
            content += f"### {item['title']}\n{item['text']}\n\n"
        content += "---\n"

    TEAM_NOTES_PATH.write_text(content, encoding="utf-8")

    # 구현 대기 파일 생성 → UserPromptSubmit 훅이 감지해 Claude에 주입
    if approved:
        pending = {
            "status": "pending",
            "topic": topic,
            "approved_at": _dt.datetime.now().isoformat(),
            "items": approved,
        }
        PENDING_IMPL_PATH.write_text(
            json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def _lookup_tc_title(nodeid: str, group: str) -> str:
    """nodeid → testcases/{group}/tc_*.md 에서 한글 제목 반환. 없으면 빈 문자열."""
    import re as _re
    parts = nodeid.split("/")
    py_file = parts[-1].split("::")[0]
    m = _re.match(r"(tc_(?:[A-Za-z]+_)?\d+)_", py_file)
    if not m:
        return ""
    tc_prefix = m.group(1)
    tc_dir = TESTCASES_DIR / group
    if not tc_dir.exists():
        return ""
    matches = sorted(tc_dir.glob(f"{tc_prefix}_*.md"))
    if not matches:
        return ""
    try:
        text = matches[0].read_text(encoding="utf-8")
    except OSError:
        return ""
    title_m = _re.search(r"^#\s+(.+)$", text, _re.MULTILINE)
    return title_m.group(1).strip() if title_m else ""


def _enrich_group_results(data: dict) -> dict:
    """execution_result.group_results 각 테스트에 한글 title 필드 추가."""
    exec_result = data.get("execution_result")
    if not exec_result or not isinstance(exec_result, dict):
        return data
    group_results = exec_result.get("group_results", {})
    if not group_results:
        return data
    for group, gdata in group_results.items():
        if not isinstance(gdata, dict):
            continue
        for test in gdata.get("tests", []):
            if not isinstance(test, dict) or test.get("title"):
                continue
            nodeid = test.get("nodeid", "")
            test["title"] = _lookup_tc_title(nodeid, group)
    return data


def build_pipeline_state() -> dict:
    """단일 파이프라인 state/pipeline.json 반환 (group_results에 한글 title 추가)."""
    data = load_json(STATE_PATH) or {}
    return _enrich_group_results(data)


def build_batch_state() -> dict:
    """병렬 파이프라인 상태 + tests/generated/ 파일 목록 반환."""
    parallel = load_json(PARALLEL_STATE_PATH) or {}
    generated_files = []
    if GENERATED_DIR.exists():
        for group_dir in sorted(GENERATED_DIR.iterdir()):
            if group_dir.is_dir() and not group_dir.name.startswith("."):
                for f in sorted(group_dir.glob("*.py")):
                    if f.name not in ("conftest.py", "__init__.py"):
                        generated_files.append({
                            "group": group_dir.name,
                            "file": f.name,
                            "path": str(f.relative_to(PROJECT_ROOT)),
                            "size": f.stat().st_size,
                        })
    # completed_count: parallel.json 값이 아닌 실제 생성 파일 수로 보정.
    # subagent 완료 후 parallel.json이 갱신되기 전에도 정확한 진행률을 표시하기 위함.
    if parallel.get("status") in (ParallelStatus.READY, "generating",  # P82: 상수 교체 ("generating"은 UI 파생 상태)
                                    ParallelStatus.TESTING, ParallelStatus.DONE):
        parallel = {**parallel, "completed_count": len(generated_files)}
    _enrich_group_results(parallel)
    return {"parallel_state": parallel, "generated_files": generated_files}


def build_pipeline_registry() -> dict:
    """프론트엔드용 파이프라인 레지스트리 상수 (P45).

    /api/pipeline_registry GET 엔드포인트가 반환하는 데이터.
    _pipeline_registry.py가 단일 소스 — 이 함수가 프론트 표현 형식으로 변환.
    constants.js가 이 값을 fetch해 PIPELINE_STEPS / STEP_LABELS 등 전역 변수를 갱신.
    """
    # 단일 파이프라인 스텝바 순서 (heal/timeout은 표시 이탈 상태이므로 제외)
    _terminal_excl = {Step.HEAL_NEEDED, Step.HEAL_FAILED, Step.TIMEOUT}
    pipeline_steps = [s.step for s in PIPELINE_STEP_DEFS if s.step not in _terminal_excl]

    # 모든 step 라벨 (heal 포함 — STEP_LABELS 전체 대체용)
    # M-2(P134): last-wins dict comprehension → STEP_DEF_BY_NAME 사용 (first-wins, STEP_DEF_BY_NAME과 동일 동작)
    step_labels: dict[str, str] = {k: v.label for k, v in STEP_DEF_BY_NAME.items()}
    # 구 step 값 호환 맵 — P58: _pipeline_registry.STEP_COMPAT이 단일 소스
    step_compat = STEP_COMPAT
    # compat step에도 라벨 추가 (STEP_LABELS[compat_step] 조회 지원)
    for alias, canonical in step_compat.items():
        step_labels.setdefault(alias, step_labels.get(canonical, alias))

    # 병렬 파이프라인 스텝바 순서
    # "generating"은 레지스트리 미등록 UI 파생 상태 (ready + files>0 조건)
    parallel_steps = [
        ParallelStatus.INIT,
        ParallelStatus.ANALYZING,
        ParallelStatus.READY,
        "generating",          # UI 파생 상태: parallel.js가 ready에서 추론
        ParallelStatus.TESTING,
        ParallelStatus.DONE,
    ]
    # P58: _pipeline_registry.PARALLEL_STEP_LABELS이 단일 소스
    parallel_step_labels = PARALLEL_STEP_LABELS

    return {
        "pipeline": {
            "steps":       pipeline_steps,
            "step_labels": step_labels,
            "step_compat": step_compat,
        },
        "parallel": {
            "steps":       parallel_steps,
            "step_labels": parallel_step_labels,
        },
    }


def list_pages() -> dict:
    """config/pages.json 반환 (_comment 등 메타 키 제외)."""
    raw = load_json(PAGES_JSON) or {}
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def list_testcase_groups() -> list:
    """testcases/ 하위 폴더별 케이스 파일 목록."""
    if not TESTCASES_DIR.exists():
        return []
    groups = []
    for d in sorted(TESTCASES_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        cases = sorted([f.name for f in d.glob("tc_*.md")])
        groups.append({"name": d.name, "cases": cases, "count": len(cases)})
    return groups


def _natural_sort_key(name: str) -> list:
    """숫자 부분을 정수로 변환해 자연 정렬 키 반환 (tc_9 < tc_10 < tc_11 보장)."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", name)]


def list_generated_groups() -> list:
    """tests/generated/ 하위 그룹별 테스트 파일 목록 반환.
    testcases/ 의 .md 파일 기준으로 유효한 파일만 집계 (잔여 파일 제외).
    """
    if not GENERATED_DIR.exists():
        return []
    groups = []
    for d in sorted(GENERATED_DIR.iterdir(), key=lambda p: _natural_sort_key(p.name)):
        if not d.is_dir() or d.name.startswith((".", "_")):
            continue
        all_py = sorted([
            f.name for f in d.glob("tc_*.py")
        ], key=_natural_sort_key)
        # testcases/{group}/tc_*.md 기준으로 유효 파일 집합 산출 (번호 prefix로 매칭)
        tc_dir = TESTCASES_DIR / d.name
        if tc_dir.exists():
            import re as _re
            def _tc_key(name):
                # tc_01_… 또는 tc_CL_01_… 형식 모두 지원 (영문 접두어 선택적)
                m = _re.match(r'^(tc_(?:[A-Za-z]+_)?\d+)_', name)
                return m.group(1) if m else None
            valid_keys = {_tc_key(f.name) for f in tc_dir.glob("tc_*.md")} - {None}
            files = [f for f in all_py if _tc_key(f) in valid_keys]
            stale_count = len(all_py) - len(files)
        else:
            files = all_py
            stale_count = 0
        if files:
            entry = {
                "name": d.name,
                "file_count": len(files),
                "files": files,
            }
            if stale_count > 0:
                entry["stale_count"] = stale_count
            groups.append(entry)
    return groups


def _is_safe_report_name(name: object) -> bool:
    """리포트 경계에서 허용하는 단일 HTML 파일명인지 확인한다."""
    return (
        isinstance(name, str)
        and is_safe_filename(name)
        and not any(ord(character) < 32 for character in name)
        and Path(name).suffix == ".html"
    )


def list_reports() -> list:
    """tests/reports/ 의 모든 일반 HTML 파일 목록 (최신순)."""
    if not REPORTS_DIR.exists():
        return []
    candidates = []
    for path in REPORTS_DIR.glob("*.html"):
        try:
            metadata = path.stat(follow_symlinks=False)
        except OSError:
            # 목록 생성 중 파일이 사라지는 정상적인 경쟁은 해당 항목만 건너뛴다.
            continue
        if stat.S_ISREG(metadata.st_mode):
            candidates.append((metadata.st_mtime, path.name, metadata.st_size))

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "name": name,
            "modified_at": datetime.fromtimestamp(mtime).isoformat(),
            "size": size,
        }
        for mtime, name, size in candidates
    ]


def build_dialogs() -> dict:
    """팀 토론 대화 payload 반환 (dialog.json은 팀 토론 전용)."""
    full_dialog = load_json(DIALOG_PATH) or {"sessions": []}
    discuss_state = load_json(DISCUSS_PATH) or {}

    # step=discussed 이고 conclusion_items 없으면 메모리에서만 파싱 (P56: GET에서 write 금지)
    # 파싱 결과는 이 호출의 반환값에만 포함되고 파일에는 기록하지 않는다.
    # 영속화가 필요하면 별도 POST 엔드포인트를 사용한다.
    if (discuss_state.get("step") == "discussed"
            and discuss_state.get("conclusion")
            and not discuss_state.get("conclusion_items")):
        discuss_state = {**discuss_state,
                         "conclusion_items": parse_conclusion_items(discuss_state["conclusion"])}

    all_sessions = full_dialog.get("sessions", [])
    team_sessions = [s for s in all_sessions if s.get("stage") == "team_discussion"]

    # discuss_state의 conclusion_items와 status를 topic이 일치하는 세션에 주입
    if discuss_state.get("topic"):
        for ts in team_sessions:
            if ts.get("topic") == discuss_state["topic"]:
                if discuss_state.get("conclusion_items"):
                    ts["conclusion_items"] = discuss_state["conclusion_items"]
                if discuss_state.get("step"):
                    ts["status"] = discuss_state["step"]
                break

    return {
        "team_sessions": team_sessions,
        "discuss_state": discuss_state,
    }
