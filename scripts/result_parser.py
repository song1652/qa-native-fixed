"""pytest JSON 리포트 파싱 공통 모듈.

05_execute.py (단일)와 99_merge.py (병렬)가 공유.
"""


def parse_results(report: dict) -> dict:
    """JSON 리포트 → {nodeid: outcome} 매핑.

    outcome 값: "passed" | "failed" | "skipped"
    """
    results = {}
    for t in report.get("tests", []):
        nodeid = t.get("nodeid", "")
        outcome = t.get("outcome", "failed")
        if outcome not in ("passed", "skipped"):
            outcome = "failed"
        results[nodeid] = outcome
    return results


def parse_durations(report: dict) -> dict:
    """JSON 리포트 → {nodeid: {setup_ms, call_ms, teardown_ms, total_ms}} 매핑."""
    out = {}
    for t in report.get("tests", []):
        nodeid = t.get("nodeid", "")
        if not nodeid:
            continue
        out[nodeid] = {
            "setup_ms":    round(t.get("setup",    {}).get("duration", 0) * 1000),
            "call_ms":     round(t.get("call",     {}).get("duration", 0) * 1000),
            "teardown_ms": round(t.get("teardown", {}).get("duration", 0) * 1000),
            "total_ms":    round(t.get("duration", 0) * 1000),
        }
    return out


def parse_skip_messages(report: dict) -> dict:
    """JSON 리포트 → {nodeid: skip_reason} (스킵 케이스만).

    pytest.skip("reason") 호출 시 call.longrepr / setup.longrepr 에서 이유 추출.
    longrepr 형식: 문자열 "('path', line, 'Skipped: reason')" 또는 단순 문자열.
    """
    import ast
    messages = {}
    for t in report.get("tests", []):
        if t.get("outcome") != "skipped":
            continue
        nodeid = t.get("nodeid", "")
        for phase in ("call", "setup"):
            phase_data = t.get(phase) or {}
            longrepr = phase_data.get("longrepr", "")
            if not longrepr:
                continue
            msg = ""
            if isinstance(longrepr, str):
                # "(path, line, 'Skipped: reason')" 튜플 문자열 형식
                try:
                    parsed = ast.literal_eval(longrepr)
                    if isinstance(parsed, tuple) and len(parsed) >= 3:
                        msg = str(parsed[2]).replace("Skipped: ", "").strip()
                    else:
                        msg = longrepr.replace("Skipped: ", "").strip()
                except Exception:
                    msg = longrepr.replace("Skipped: ", "").strip()
            elif isinstance(longrepr, (list, tuple)) and len(longrepr) >= 3:
                msg = str(longrepr[2]).replace("Skipped: ", "").strip()
            else:
                msg = str(longrepr).replace("Skipped: ", "").strip()
            if msg:
                messages[nodeid] = msg
                break
    return messages
