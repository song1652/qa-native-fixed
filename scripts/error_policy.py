"""Conservative web failure classification. Classification never replays actions."""
import re


_COPY = {
    'browser_unavailable': ('브라우저 실행 확인', 'Playwright 브라우저 설치와 실행 환경을 확인한 뒤 다시 시작하세요.', 'check_environment'),
    'session_lost': ('브라우저 세션 연결 끊김', '브라우저 상태와 실행 로그를 확인하고 필요한 세션을 다시 연결하세요.', 'reconnect_browser'),
    'transport': ('통신 연결 오류', '대상 웹사이트와 브라우저 연결을 확인하세요. 완료 여부가 불분명한 동작은 자동 반복하지 않습니다.', 'check_environment'),
    'locator': ('요소 확인 필요', '선택한 페이지의 요소와 Locator를 검토하세요.', 'review_locator'),
    'assertion': ('검증 결과 불일치', '실제 웹 결과와 테스트의 기대값을 비교하세요.', 'review_assertion'),
    'configuration': ('실행 설정 확인', '테스트 파일, 실행 옵션과 Playwright 설정을 확인하세요.', 'review_configuration'),
    'timeout': ('실행 제한 시간 초과', '실행 로그와 웹사이트 상태를 확인한 뒤 필요한 작업을 다시 시작하세요.', 'inspect_log'),
    'interrupted': ('실행 중단', '완료된 결과와 실행 로그를 확인하세요. 남은 동작은 자동으로 실행하지 않습니다.', 'inspect_log'),
    'unknown': ('실행 오류 확인', '실행 로그에서 원인을 확인하세요. 원인이 확인되기 전에는 자동 복구하지 않습니다.', 'inspect_log'),
}


def classify_error(error, status=None):
    """Return category/title/message/action/can_heal/read_retryable only."""
    if isinstance(error, dict):
        text = f"{error.get('error_type', '')} {error.get('error', '')}".lower()
    else:
        text = f"{type(error).__name__ if isinstance(error, BaseException) else ''} {error}".lower()
    category = 'unknown'
    if status in ('timed_out', 'timeout'):
        category = 'timeout'
    elif status in ('interrupted', 'cancelled'):
        category = 'interrupted'
    elif 'assertionerror' in text or re.match(r'^\s*(?:e\s+)?assert\s', text):
        category = 'assertion'
    elif any(token in text for token in (
        'collectionerror', 'syntaxerror', 'importerror', 'modulenotfounderror', 'filenotfounderror',
        'invalid selector', 'invalid test file', 'no tests found', 'pytest usage error',
        'no tests collected', 'invalid configuration', 'unrecognized arguments',
    )):
        category = 'configuration'
    elif any(token in text for token in (
        "executable doesn't exist", 'browser executable not found', 'browsertype.launch',
        'playwright install', 'host system is missing dependencies',
    )):
        category = 'browser_unavailable'
    elif any(token in text for token in (
        'targetclosederror', 'target page, context or browser has been closed',
        'browser has been closed', 'browser disconnected', 'session closed',
    )):
        category = 'session_lost'
    elif any(token in text for token in (
        'connectionreset', 'connection reset', 'err_connection_reset', 'readtimeout',
        'read timed out', 'connectionrefused', 'connection refused', 'err_connection_refused',
        'remotedisconnected', 'brokenpipe', 'socket hang up', 'err_name_not_resolved',
    )):
        category = 'transport'
    elif any(token in text for token in (
        'strict mode violation', 'waiting for locator(', 'waiting for get_by_',
        'element is not attached to the dom', 'element is not visible',
    )):
        category = 'locator'
    elif any(token in text for token in ('timeouterror', 'timeoutexpired', 'timeout ', 'timed out')):
        category = 'timeout'
    title, message, action = _COPY[category]
    read_retryable = category == 'transport' and any(token in text for token in (
        'connectionreset', 'connection reset', 'err_connection_reset', 'readtimeout',
        'read timed out', 'remotedisconnected',
    ))
    return dict(category=category, title=title, message=message, action=action,
                can_heal=category == 'locator', read_retryable=read_retryable)


def errors_from_report(report):
    """Keep every failing test phase and collection error for recovery admission."""
    errors = []
    for test in report.get("tests", []):
        phases = [phase for phase in ("setup", "call", "teardown")
                  if (test.get(phase) or {}).get("outcome") in ("failed", "error")]
        if not phases and test.get("outcome") not in ("passed", "skipped"):
            phases = ["call"]
        for phase in phases:
            data = test.get(phase) or {}
            message = data.get("longrepr") or (data.get("crash") or {}).get("message") or "Unknown error"
            errors.append({"nodeid": test.get("nodeid", ""),
                           "test_name": test.get("nodeid", "").split("::")[-1],
                           "phase": phase, "error": str(message)})
    for collector in report.get("collectors", []):
        if collector.get("outcome") == "failed":
            errors.append({"nodeid": collector.get("nodeid", ""), "phase": "collection",
                           "error_type": "CollectionError", "error": str(collector.get("longrepr") or "Collection failed")})
    return errors


def recovery_for_result(result):
    """Accept an execution result or its state envelope; mixed failures block healing."""
    if not isinstance(result, dict):
        return classify_error('')
    execution = result.get('execution_result') or result.get('execute_results') or result
    if not isinstance(execution, dict):
        return classify_error('')
    status = result.get('status') or execution.get('status')
    if status in ('timed_out', 'timeout', 'interrupted', 'cancelled'):
        return classify_error('', status=status)
    errors = execution.get('errors', [])
    if not isinstance(errors, list):
        return classify_error('')
    errors = list(errors)
    groups = execution.get('group_results') or {}
    if isinstance(groups, dict):
        for group in groups.values():
            if isinstance(group, dict):
                errors.extend(test for test in group.get('tests', [])
                              if isinstance(test, dict) and (test.get('outcome') in ('failed', 'error')
                                                            or test.get('passed') is False))
    exit_code = execution.get('exit_code')
    if exit_code is None:
        exit_code = result.get('exit_code')
    if isinstance(exit_code, int) and exit_code not in (0, 1):
        collection_failed = any(isinstance(error, dict) and (
            error.get('phase') == 'collection' or error.get('error_type') == 'CollectionError') for error in errors)
        if exit_code == 2 and collection_failed:
            return classify_error('CollectionError')
        if exit_code == 2 or exit_code < 0:
            return classify_error('', status='interrupted')
        if exit_code in (4, 5):
            return classify_error('pytest usage error' if exit_code == 4 else 'no tests collected')
        return classify_error('')  # Pytest internal errors cannot admit partial locator healing.
    if status in ('passed', 'running'):
        return classify_error('')
    classified = [classify_error(error) for error in errors]
    if not classified:
        recovery = classify_error(result.get('error') or execution.get('error', ''), status=status)
        recovery['can_heal'] = False  # No failed test/locator is available to repair.
        return recovery
    if all(item['can_heal'] for item in classified):
        return classified[0]
    return next(item for item in classified if not item['can_heal'])
