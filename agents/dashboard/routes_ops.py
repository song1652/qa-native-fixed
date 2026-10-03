"""routes_ops.py — OpsRoutesMixin (serve.py Phase-6 분리).

운영 POST 핸들러 — pages CRUD, 파이프라인 실행/리셋, 팀 토론 등.
DashboardHandler가 이 Mixin을 상속받아 사용한다.

설계 원칙:
- 이 모듈은 serve.py를 import하지 않는다 (순환 import 방지).
- __init__ 정의 없음 — MRO에서 BaseHTTPRequestHandler.__init__ 사용.
"""
from __future__ import annotations

import json
from functools import wraps

import _paths
from _paths import (
    write_state as _safe_write_json,
    update_state as _safe_update_json,
    reset_state,
)
from _python import PYTHON_EXE
from _pipeline_registry import (
    ParallelStatus,
    make_initial_pipeline_state,
    RESETTABLE_PARALLEL_STATUSES,
)
from _validators import is_valid_url, is_valid_group_name, is_safe_filename
from dash_state import load_json, finalize_team_notes
from dash_http import _read_body
from dash_procs import (
    start_execution, execution_status, cancel_execution, run_when_idle,
    _is_script_running,
    _is_spawned_pid,
)


def _inactive_execution(method):
    @wraps(method)
    def guarded(self):
        if not run_when_idle(lambda: method(self)):
            self._serve_bytes(b'{"ok":false,"error":"Cancel the active execution before resetting"}',
                              "application/json; charset=utf-8")
    return guarded


class OpsRoutesMixin:
    """운영 POST 핸들러 메서드 모음.

    DashboardHandler(OpsRoutesMixin, ...) 형태로 사용.
    self._serve_bytes 는 DashboardHandler infra layer가 제공.
    """

    def _get_execution_status(self):
        result = {"ok": True, "execution": execution_status()}
        self._serve_bytes(json.dumps(result, ensure_ascii=False).encode("utf-8"),
                          "application/json; charset=utf-8")

    def _post_cancel(self):
        result = cancel_execution(_read_body(self).get("run_id"))
        self._serve_bytes(json.dumps(result, ensure_ascii=False).encode("utf-8"),
                          "application/json; charset=utf-8")

    # ── Pages CRUD ────────────────────────────────────────────────

    def _post_pages_add(self):
        body = _read_body(self)
        group   = body.get("group", "").strip()
        url     = body.get("url", "").strip()
        notes   = body.get("notes", "").strip()
        spa     = bool(body.get("spa", False))
        project = body.get("project", "").strip()

        if not group or not url:
            self._serve_bytes(b'{"ok":false,"error":"group and url required"}', "application/json; charset=utf-8"); return
        if not is_valid_group_name(group) or group.startswith("_"):
            self._serve_bytes(b'{"ok":false,"error":"invalid group name"}', "application/json; charset=utf-8"); return
        if not is_valid_url(url):
            self._serve_bytes(b'{"ok":false,"error":"url must start with http:// or https://"}', "application/json; charset=utf-8"); return
        if project and not is_valid_group_name(project):
            self._serve_bytes(b'{"ok":false,"error":"project name: alphanumeric/underscore/hyphen only"}', "application/json; charset=utf-8"); return

        # pages.json 파싱 실패 시 설정 소실 방지
        if _paths.PAGES_JSON.exists():
            raw = load_json(_paths.PAGES_JSON)
            if raw is None:
                self._serve_bytes(
                    b'{"ok":false,"error":"pages.json \xed\x8c\x8c\xec\x8b\xb1 \xec\x8b\xa4\xed\x8c\xa8 \xe2\x80\x94 \xec\x88\x98\xeb\x8f\x99 \xed\x99\x95\xec\x9d\xb8 \xed\x95\x84\xec\x9a\x94"}',
                    "application/json; charset=utf-8"); return

        # RMW 원자적 처리 (락 보유 중 읽기+중복 체크+쓰기)
        error_msg = None
        def _add_mutator(cur: dict) -> dict:
            nonlocal error_msg
            if group in cur:
                error_msg = f"'{group}' 그룹이 이미 존재합니다"
                return cur
            entry: dict = {"url": url, "spa": spa, "preconditions": [], "notes": notes}
            if project:
                entry["project"] = project
            cur[group] = entry
            return cur

        _safe_update_json(_paths.PAGES_JSON, _add_mutator)
        if error_msg:
            self._serve_bytes(
                json.dumps({"ok": False, "error": error_msg}, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8"); return

        (_paths.TESTCASES_DIR / group).mkdir(parents=True, exist_ok=True)
        print(f"[Dashboard] 페이지 추가: {group} → {url}")
        self._serve_bytes(
            json.dumps({"ok": True, "group": group}, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8")

    def _post_pages_update(self):
        body    = _read_body(self)
        group   = body.get("group", "").strip()
        url     = body.get("url", "").strip()
        notes   = body.get("notes", "").strip()
        spa     = bool(body.get("spa", False))
        project = body.get("project", "").strip()

        if not group or not url:
            self._serve_bytes(b'{"ok":false,"error":"group and url required"}', "application/json; charset=utf-8"); return
        if not is_valid_group_name(group) or group.startswith("_"):
            self._serve_bytes(b'{"ok":false,"error":"invalid group name"}', "application/json; charset=utf-8"); return
        if not is_valid_url(url):
            self._serve_bytes(b'{"ok":false,"error":"url must start with http:// or https://"}', "application/json; charset=utf-8"); return
        if project and not is_valid_group_name(project):
            self._serve_bytes(b'{"ok":false,"error":"project name: alphanumeric/underscore/hyphen only"}', "application/json; charset=utf-8"); return

        # pages.json 파싱 실패 시 설정 소실 방지 (P54)
        if _paths.PAGES_JSON.exists():
            raw = load_json(_paths.PAGES_JSON)
            if raw is None:
                self._serve_bytes(
                    b'{"ok":false,"error":"pages.json \xed\x8c\x8c\xec\x8b\xb1 \xec\x8b\xa4\xed\x8c\xa8 \xe2\x80\x94 \xec\x88\x98\xeb\x8f\x99 \xed\x99\x95\xec\x9d\xb8 \xed\x95\x84\xec\x9a\x94"}',
                    "application/json; charset=utf-8"); return

        error_msg = None
        def _update_mutator(cur: dict) -> dict:
            nonlocal error_msg
            if group not in cur:
                error_msg = f"'{group}' 없음"
                return cur
            existing = cur[group] if isinstance(cur[group], dict) else {}
            entry: dict = {
                "url": url,
                "spa": spa,
                "preconditions": existing.get("preconditions", []),
                "notes": notes,
            }
            if project:
                entry["project"] = project
            cur[group] = entry
            return cur

        _safe_update_json(_paths.PAGES_JSON, _update_mutator)
        if error_msg:
            self._serve_bytes(
                json.dumps({"ok": False, "error": error_msg}, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8"); return

        print(f"[Dashboard] 페이지 수정: {group} → {url}")
        self._serve_bytes(
            json.dumps({"ok": True, "group": group}, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8")

    def _post_pages_delete(self):
        body = _read_body(self)
        group = body.get("group", "").strip()
        if not group or not is_valid_group_name(group) or group.startswith("_"):
            self._serve_bytes(b'{"ok":false,"error":"valid group required"}', "application/json; charset=utf-8"); return

        # pages.json 파싱 실패 시 설정 소실 방지 (P54)
        if _paths.PAGES_JSON.exists():
            raw = load_json(_paths.PAGES_JSON)
            if raw is None:
                self._serve_bytes(
                    b'{"ok":false,"error":"pages.json \xed\x8c\x8c\xec\x8b\xb1 \xec\x8b\xa4\xed\x8c\xa8 \xe2\x80\x94 \xec\x88\x98\xeb\x8f\x99 \xed\x99\x95\xec\x9d\xb8 \xed\x95\x84\xec\x9a\x94"}',
                    "application/json; charset=utf-8"); return

        # RMW 원자적 처리
        error_msg = None
        def _del_mutator(cur: dict) -> dict:
            nonlocal error_msg
            if group not in cur:
                error_msg = f"'{group}' 없음"
                return cur
            del cur[group]
            return cur

        _safe_update_json(_paths.PAGES_JSON, _del_mutator)
        if error_msg:
            self._serve_bytes(
                json.dumps({"ok": False, "error": error_msg}, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8"); return

        print(f"[Dashboard] 페이지 삭제: {group}")
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    # ── 대화·토론 핸들러 ──────────────────────────────────────────

    @_inactive_execution
    def _post_reset(self):
        empty = {"pipeline_url": "", "started_at": "", "sessions": []}
        _safe_write_json(_paths.DIALOG_PATH, empty)
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    def _post_discuss_start(self):
        import datetime
        body = _read_body(self)
        topic = body.get("topic", "").strip()
        if not topic:
            self._serve_bytes(b'{"ok":false,"error":"topic required"}',
                              "application/json; charset=utf-8")
            return

        history = []
        if _paths.DISCUSS_STATE.exists():
            try:
                prev = json.loads(_paths.DISCUSS_STATE.read_text(encoding="utf-8"))
                history = prev.get("history", [])
                if prev.get("step") in ("approved", "rejected", "discussed"):
                    history.append({k: v for k, v in prev.items() if k != "history"})
            except Exception:
                pass

        discuss = {
            "topic": topic, "step": "pending", "conclusion": "",
            "rejection_reason": "", "rejection_count": 0,
            "created_at": datetime.datetime.now().isoformat(),
            "history": history,
        }
        _safe_write_json(_paths.DISCUSS_STATE, discuss)

        # Claude Code UserPromptSubmit 훅(check_pending_discuss.py)이
        # 다음 프롬프트 제출 시 자동으로 토론 시작을 Claude에게 주입한다.
        self._serve_bytes(b'{"ok":true}',
                          "application/json; charset=utf-8")

    def _post_discuss_vote_item(self):
        body = _read_body(self)
        item_id = int(body.get("item_id", -1))
        vote    = body.get("vote", "")  # "approve" | "reject"

        if not _paths.DISCUSS_STATE.exists():
            self._serve_bytes(
                json.dumps({"ok": False, "error": "state/discuss.json 없음"}, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
            return

        # P55: 비원자 read_text+write → _safe_update_json 원자적 RMW
        _result: dict = {}

        def _mutate_vote(s: dict) -> dict:
            items = [dict(i) for i in s.get("conclusion_items", [])]
            for item in items:
                if item["id"] == item_id:
                    item["status"] = "approved" if vote == "approve" else "rejected"
                    break
            s = {**s, "conclusion_items": items}
            all_voted = bool(items) and all(i["status"] != "pending" for i in items)
            if all_voted:
                finalize_team_notes(s)
                s["step"] = "approved"
            _result["all_voted"] = all_voted
            return s

        _safe_update_json(_paths.DISCUSS_STATE, _mutate_vote)
        self._serve_bytes(
            json.dumps({"ok": True, "all_voted": _result.get("all_voted", False)},
                       ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _post_discuss_reject(self):
        body = _read_body(self)
        reason = body.get("reason", "").strip()
        if not _paths.DISCUSS_STATE.exists():
            self._serve_bytes(
                json.dumps({"ok": False, "error": "state/discuss.json 없음"}, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
            return
        # P55: 비원자 read_text+write → _safe_update_json 원자적 RMW
        _safe_update_json(_paths.DISCUSS_STATE, lambda s: {
            **s,
            "step": "rejected",
            "rejection_reason": reason,
            "rejection_count": s.get("rejection_count", 0) + 1,
        })
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    # ── 파이프라인 실행 ───────────────────────────────────────────

    def _post_run_qa(self):
        # P77: 중복 spawn 방지 — 이미 실행 중이면 거부
        if _is_script_running("run_qa"):
            self._serve_bytes(
                b'{"ok":false,"error":"run_qa already running"}',
                "application/json; charset=utf-8")
            return
        body = _read_body(self)
        url = body.get("url", "").strip()
        cases_dir = body.get("cases_dir", "").strip()
        if url and not is_valid_url(url):
            self._serve_bytes(
                b'{"ok":false,"error":"url must start with http:// or https://"}',
                "application/json; charset=utf-8")
            return
        if cases_dir and not is_valid_group_name(cases_dir):
            self._serve_bytes(
                b'{"ok":false,"error":"invalid cases_dir format"}',
                "application/json; charset=utf-8")
            return
        if not url or not cases_dir:
            self._serve_bytes(
                b'{"ok":false,"error":"url and cases_dir required"}',
                "application/json; charset=utf-8")
            return
        cases_path = _paths.TESTCASES_DIR / cases_dir
        if not cases_path.exists():
            self._serve_bytes(
                json.dumps({"ok": False, "error": f"testcases/{cases_dir} not found"}, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
            return
        script = _paths.PROJECT_ROOT / "run_qa.py"
        result = start_execution(
            [PYTHON_EXE, "-u", str(script), "--url", url, "--cases", str(cases_path)],
            "run_qa", groups=[cases_dir], legacy_log="run_qa.txt")
        self._serve_bytes(json.dumps(result, ensure_ascii=False).encode("utf-8"),
                          "application/json; charset=utf-8")

    def _post_run_qa_parallel(self):
        # P77: 중복 spawn 방지
        if _is_script_running("run_qa_parallel"):
            self._serve_bytes(
                b'{"ok":false,"error":"run_qa_parallel already running"}',
                "application/json; charset=utf-8")
            return
        result = start_execution(
            [PYTHON_EXE, "-u", str(_paths.PROJECT_ROOT / "run_qa_parallel.py")],
            "run_qa_parallel", legacy_log="run_parallel.txt")
        self._serve_bytes(json.dumps(result, ensure_ascii=False).encode("utf-8"),
                          "application/json; charset=utf-8")

    def _post_run_log(self):
        body = _read_body(self)
        run_id = body.get("run_id")
        if run_id:
            from run_results import execution_result_path
            try:
                execution_result_path(_paths.PROJECT_ROOT, run_id)
            except ValueError:
                self._serve_bytes(b'{"ok":false,"log":""}', "application/json; charset=utf-8")
                return
            log_path = _paths.LOGS_DIR / "runs" / f"{run_id}.txt"
            paths = [log_path, log_path.with_name(f"{run_id}-headless.txt")]
            payload = {"ok": any(path.is_file() for path in paths),
                       "log": "\n".join(path.read_text(encoding="utf-8", errors="replace")
                                         for path in paths if path.is_file())}
            self._serve_bytes(json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                              "application/json; charset=utf-8")
            return
        log_name = body.get("log", "run_qa.txt")
        if not is_safe_filename(log_name):
            self._serve_bytes(b'{"ok":false,"log":""}', "application/json; charset=utf-8")
            return
        log_path = _paths.LOGS_DIR / log_name
        if log_path.exists():
            content = log_path.read_text(encoding="utf-8", errors="replace")
            self._serve_bytes(
                json.dumps({"ok": True, "log": content}, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8"
            )
        else:
            self._serve_bytes(b'{"ok":false,"log":""}', "application/json; charset=utf-8")

    # ── 리셋 핸들러 ───────────────────────────────────────────────

    @_inactive_execution
    def _post_reset_all(self):
        empty = {"pipeline_url": "", "started_at": "", "sessions": []}
        _safe_write_json(_paths.DIALOG_PATH, empty)
        # FSM 전이 검증을 건너뛰는 reset_state() 사용 이유: write_state()는
        # "generated"→"init" 같은 전이가 VALID_TRANSITIONS에 없어 ValueError 발생.
        reset_state(_paths.PIPELINE_STATE, make_initial_pipeline_state())
        reset_state(_paths.PARALLEL_STATE,
                    {"status": ParallelStatus.EMPTY, "total_count": 0, "targets": []})
        heal_ctx = _paths.PROJECT_ROOT / "state" / "heal_context.json"
        if heal_ctx.exists():
            heal_ctx.unlink()
        if _paths.QUICK_STATE.exists():
            _paths.QUICK_STATE.unlink()
        _safe_write_json(_paths.HEAL_STATS_PATH, {"version": 1, "patterns": {}})
        _safe_write_json(_paths.RUN_HISTORY, [])
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    @_inactive_execution
    def _post_pipeline_reset(self):
        # 팩토리 함수로 단일화 (P39). FSM 검증 우회 이유는 _post_reset_all 참조.
        reset_state(_paths.PIPELINE_STATE, make_initial_pipeline_state())
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    @_inactive_execution
    def _post_parallel_reset(self):
        init_state = {"status": ParallelStatus.EMPTY, "total_count": 0, "targets": []}
        reset_state(_paths.PARALLEL_STATE, init_state)
        heal_ctx = _paths.PROJECT_ROOT / "state" / "heal_context.json"
        if heal_ctx.exists():
            heal_ctx.unlink()
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    def _post_quick_reset(self):
        body = _read_body(self)
        current = execution_status()
        if current.get("status") == "running":
            run_id = body.get("run_id")
            if not run_id and body.get("pid") == current.get("pid"):
                run_id = current.get("run_id")
            result = cancel_execution(run_id)
            self._serve_bytes(json.dumps(result, ensure_ascii=False).encode("utf-8"),
                              "application/json; charset=utf-8")
            return
        try:
            pid = int(body["pid"]) if body.get("pid") else None
        except (ValueError, TypeError):
            self._serve_bytes(b'{"ok":false,"error":"Invalid PID"}',
                              "application/json; charset=utf-8", status=400)
            return
        if pid and not _is_spawned_pid(pid):
            self._serve_bytes(b'{"ok":false,"error":"Process is not owned by this server"}',
                              "application/json; charset=utf-8", status=403)
            return
        def reset_quick():
            _paths.QUICK_STATE.unlink(missing_ok=True)
        if not run_when_idle(reset_quick):
            self._serve_bytes(b'{"ok":false,"error":"QA execution already running"}',
                              "application/json; charset=utf-8")
            return
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    def _post_heal_stats_reset(self):
        _safe_write_json(_paths.HEAL_STATS_PATH, {"version": 1, "patterns": {}})
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    def _post_run_history_reset(self):
        _safe_write_json(_paths.RUN_HISTORY, [])
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    def _post_discuss_reset(self):
        # discuss.json 초기화 (topic/step/conclusion 등 모든 상태 제거)
        _safe_write_json(_paths.DISCUSS_STATE, {})
        # dialog.json의 team_discussion 세션도 제거
        dialog = load_json(_paths.DIALOG_PATH) or {"sessions": []}
        dialog["sessions"] = [
            s for s in dialog.get("sessions", [])
            if s.get("stage") != "team_discussion"
        ]
        _safe_write_json(_paths.DIALOG_PATH, dialog)
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    # ── 병렬·빠른 실행 ────────────────────────────────────────────

    def _post_run_merge(self):
        # P77: 중복 spawn 방지
        if _is_script_running("run_merge"):
            self._serve_bytes(
                b'{"ok":false,"error":"99_merge already running"}',
                "application/json; charset=utf-8")
            return
        merge_script = _paths.PROJECT_ROOT / "parallel" / "99_merge.py"
        if not merge_script.exists():
            self._serve_bytes(b'{"ok":false,"error":"99_merge.py not found"}',
                              "application/json; charset=utf-8")
            return
        # C-3(P99): heal_count 리셋은 "새 실행" 시작 시에만.
        # M-4(P121): RESETTABLE_PARALLEL_STATUSES를 단일 소스에서 임포트.
        def prepare():
            if _paths.PARALLEL_STATE.exists():
                _cur_status = (load_json(_paths.PARALLEL_STATE) or {}).get("status", "")
                if _cur_status in RESETTABLE_PARALLEL_STATUSES:
                    _safe_update_json(_paths.PARALLEL_STATE, lambda s: {**s, "heal_count": 0})

        result = start_execution([PYTHON_EXE, "-u", str(merge_script)],
                                 "run_merge", legacy_log="merge.txt", prepare=prepare)
        self._serve_bytes(json.dumps(result, ensure_ascii=False).encode("utf-8"),
                          "application/json; charset=utf-8")

    def _post_merge_log(self):
        log_path = _paths.LOGS_DIR / "merge.txt"
        if log_path.exists():
            content = log_path.read_text(encoding="utf-8", errors="replace")
            self._serve_bytes(
                json.dumps({"ok": True, "log": content}, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8"
            )
        else:
            self._serve_bytes(b'{"ok":false,"log":""}',
                              "application/json; charset=utf-8")

    def _post_run_quick(self):
        # P77: 중복 spawn 방지
        if _is_script_running("run_quick"):
            self._serve_bytes(
                b'{"ok":false,"error":"run_quick already running"}',
                "application/json; charset=utf-8")
            return
        body = _read_body(self)
        groups = body.get("groups", [])
        if not groups:
            self._serve_bytes(
                b'{"ok":false,"error":"groups required"}',
                "application/json; charset=utf-8")
            return
        # 그룹명 형식 검증 (경로 탈출 방지)
        invalid = [g for g in groups if not is_valid_group_name(g)]
        if invalid:
            self._serve_bytes(
                json.dumps({"ok": False, "error": f"잘못된 그룹명: {', '.join(invalid)}"},
                           ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
            return
        # 폴더 존재 검증
        missing = [g for g in groups if not (_paths.GENERATED_DIR / g).is_dir()]
        if missing:
            self._serve_bytes(
                json.dumps({"ok": False, "error": f"존재하지 않는 폴더: {', '.join(missing)}"},
                           ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
            return

        # M-1(P107): heal_count 리셋은 RESETTABLE 상태에서만.
        # M-4(P121): RESETTABLE_PARALLEL_STATUSES 단일 소스 사용.
        def prepare():
            if _paths.QUICK_STATE.exists():
                _quick_status = (load_json(_paths.QUICK_STATE) or {}).get("status", "")
                if _quick_status in RESETTABLE_PARALLEL_STATUSES:
                    _safe_update_json(_paths.QUICK_STATE, lambda s: {**s, "heal_count": 0})

        merge_script = _paths.PROJECT_ROOT / "parallel" / "99_merge.py"
        no_heal = body.get("no_heal", False)
        cmd = [PYTHON_EXE, "-u", str(merge_script), "--quick", "--group"] + groups
        if no_heal:
            cmd.append("--no-heal")
        result = start_execution(cmd, "run_quick", groups=groups, legacy_log="quick_run.txt", prepare=prepare)
        self._serve_bytes(json.dumps(result, ensure_ascii=False).encode("utf-8"),
                          "application/json; charset=utf-8")
