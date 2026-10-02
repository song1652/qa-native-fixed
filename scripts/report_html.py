"""공통 HTML 리포트 생성 모듈.

05_execute.py (단일)와 99_merge.py (병렬)가 공유.
그룹 접기/펼치기, All/Pass/Fail 필터, 그룹 내 페이지네이션 지원.
Playwright 스타일 아티팩트: trace step 타이밍 / screenshot / video / trace 링크.
"""
import html as _html
import re
import zipfile
import json as _json
from pathlib import Path

_re_step = re.compile(r"^\s*\d+[\.\)]\s*")
_re_bullet = re.compile(r"^\s*[-*]\s*")
_re_camel = re.compile(r"(?<!^)(?=[A-Z])")

CASES_PER_PAGE = 20

# Playwright API → 친화적 이름 매핑
_API_MAP = {
    "Page.navigate": "page.goto",
    "Page.click": "page.click",
    "Page.fill": "page.fill",
    "Page.type": "page.type",
    "Page.press": "page.press",
    "Page.check": "page.check",
    "Page.uncheck": "page.uncheck",
    "Page.selectOption": "page.select_option",
    "Page.hover": "page.hover",
    "Page.waitForSelector": "page.wait_for_selector",
    "Page.waitForURL": "page.wait_for_url",
    "Page.waitForLoadState": "page.wait_for_load_state",
    "Page.waitForTimeout": "page.wait_for_timeout",
    "Page.screenshot": "page.screenshot",
    "Page.evaluate": "page.evaluate",
    "Page.locator": "page.locator",
    "Page.goto": "page.goto",
    "Frame.click": "frame.click",
    "Frame.fill": "frame.fill",
    "Frame.waitForSelector": "frame.wait_for_selector",
    "Locator.click": "locator.click",
    "Locator.fill": "locator.fill",
    "Locator.waitFor": "locator.wait_for",
    "Locator.textContent": "locator.text_content",
    "Locator.getAttribute": "locator.get_attribute",
    "Locator.isVisible": "locator.is_visible",
    "Locator.evaluate": "locator.evaluate",
    "ElementHandle.click": "element.click",
}


def _esc(text: str) -> str:
    return _html.escape(str(text), quote=True)


def _strip_prefix(text: str) -> str:
    t = _re_step.sub("", text)
    t = _re_bullet.sub("", t)
    return t.strip()


def _friendly_name(api_name: str) -> str:
    if api_name in _API_MAP:
        return _API_MAP[api_name]
    if "." in api_name:
        cls, method = api_name.split(".", 1)
        snake = _re_camel.sub("_", method).lower()
        return f"{cls.lower()}.{snake}"
    return api_name.lower()


def _fmt_ms(ms: int) -> str:
    if ms < 1000:
        return f"{ms}ms"
    return f"{ms / 1000:.1f}s"


def parse_trace_steps(trace_zip_path: str) -> list:
    """trace.zip에서 Playwright action 이벤트를 추출해 [{name, duration_ms}] 반환.

    Playwright Python 트레이스 포맷:
      {"type":"before","callId":"call@7","startTime":204.744,"class":"BrowserContext","method":"newPage",...}
      {"type":"after","callId":"call@7","endTime":230.598,...}
    before/after를 callId로 매칭해 duration 계산.
    """
    steps = []
    try:
        with zipfile.ZipFile(trace_zip_path) as zf:
            trace_files = [n for n in zf.namelist() if n.endswith(".trace")]
            for tf in trace_files:
                data = zf.read(tf).decode("utf-8", errors="replace")
                befores = {}  # callId -> {name, startTime}
                for line in data.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = _json.loads(line)
                    except Exception:
                        continue
                    ev_type = ev.get("type")
                    if ev_type == "before":
                        call_id = ev.get("callId")
                        if not call_id:
                            continue
                        # title이 있으면 우선 사용 (Expect "to_be_visible" 등)
                        title = ev.get("title", "")
                        if not title:
                            cls = ev.get("class", "")
                            method = ev.get("method", "")
                            api = f"{cls}.{method}" if cls and method else method
                            title = _friendly_name(api) if api else ""
                        if title:
                            befores[call_id] = {
                                "name": title,
                                "startTime": ev.get("startTime", 0),
                            }
                    elif ev_type == "after":
                        call_id = ev.get("callId")
                        if call_id and call_id in befores:
                            before_ev = befores.pop(call_id)
                            end = ev.get("endTime", 0)
                            dur_ms = round(end - before_ev["startTime"]) if end > before_ev["startTime"] else 0
                            steps.append({
                                "name": before_ev["name"],
                                "duration_ms": dur_ms,
                            })
    except Exception:
        pass
    return steps


def _artifact_http_path(abs_path: str, subdir: str) -> str:
    """절대 파일 경로 → serve.py HTTP 상대 경로 변환.

    /…/tests/screenshots/foo.png  →  /screenshots/foo.png
    /…/tests/videos/foo.webm      →  /videos/foo.webm
    """
    p = Path(abs_path)
    return f"/{subdir}/{p.name}"


def _build_artifact_panel(uid: str, duration: dict | None, artifacts: dict) -> str:
    """실패 TC의 아티팩트 패널 HTML 생성 (screenshot / video / trace 링크)."""
    screenshot_path = artifacts.get("screenshot_path", "")
    trace_path = artifacts.get("trace_path", "")
    video_path = artifacts.get("video_path", "")

    parts = []

    # ── Screenshots ────────────────────────────────────────────────
    if screenshot_path and Path(screenshot_path).exists():
        # file:// 대신 serve.py HTTP 경로 사용 (iframe CSP 통과)
        ss_src = _artifact_http_path(screenshot_path, "screenshots")
        trace_btn = ""
        if trace_path:
            trace_btn = (
                f'<a class="trace-link" '
                f'data-trace-path="{_esc(trace_path)}" '
                f'href="javascript:void(0)">trace 명령 복사</a>'
            )
        parts.append(
            f'<div class="artifact-sub">'
            f'<div class="artifact-sub-title">스크린샷</div>'
            f'<div class="screenshot-wrap">'
            f'<img src="{_esc(ss_src)}" class="screenshot-thumb" alt="screenshot">'
            f'</div>'
            f'{trace_btn}'
            f'</div>'
        )

    # ── Videos ────────────────────────────────────────────────────
    if video_path and Path(video_path).exists():
        vid_src = _artifact_http_path(video_path, "videos")
        parts.append(
            f'<div class="artifact-sub">'
            f'<div class="artifact-sub-title">영상</div>'
            f'<video src="{_esc(vid_src)}" controls class="artifact-video"></video>'
            f'<a href="{_esc(vid_src)}" class="artifact-dl" download>영상 다운로드</a>'
            f'</div>'
        )

    if not parts:
        return ""
    return f'<div class="artifact-panel">{"".join(parts)}</div>'


def case_row(case: dict, uid: str, outcome,
             duration: dict | None = None,
             artifacts: dict | None = None) -> str:
    """테스트 케이스 행 HTML 생성.

    outcome: "passed" | "failed" | "skipped"  또는 bool (하위 호환)
    duration: {setup_ms, call_ms, teardown_ms, total_ms} | None
    artifacts: {screenshot_path, trace_path, video_path, trace_steps} | None
    """
    if isinstance(outcome, bool):
        outcome = "passed" if outcome else "failed"
    _cls_map = {"passed": "pass", "failed": "fail", "skipped": "skip"}
    _txt_map = {"passed": "통과", "failed": "실패", "skipped": "건너뜀"}
    status_cls = _cls_map.get(outcome, "fail")
    badge_txt = _txt_map.get(outcome, "실패")

    title = case.get("title", "제목 없음")
    precondition = case.get("precondition", "")
    steps = case.get("steps", [])
    expected = case.get("expected", "")
    skip_reason = case.get("skip_reason", "") if outcome == "skipped" else ""

    clean_steps = [_esc(_strip_prefix(s)) for s in steps if s.strip()]
    steps_html = "".join(f"<li>{s}</li>" for s in clean_steps) if clean_steps else "<li>-</li>"

    pre_lines = [_esc(_strip_prefix(l)) for l in precondition.splitlines() if l.strip()]
    pre_content = "<br>".join(pre_lines)
    pre_html = (
        f'<div class="detail-row">'
        f'<span class="detail-label">사전 조건</span>'
        f'<span class="detail-val">{pre_content}</span>'
        f'</div>'
        if pre_content else ""
    )

    exp_raw = expected.replace("\\n", "\n")
    exp_lines = [_esc(_strip_prefix(l)) for l in exp_raw.splitlines() if l.strip()]
    exp_content = "<br>".join(exp_lines)

    skip_reason_html = (
        f'<div class="detail-row">'
        f'<span class="detail-label">건너뛴 이유</span>'
        f'<span class="detail-val" style="color:var(--skip);">{_esc(skip_reason)}</span>'
        f'</div>'
        if skip_reason else ""
    )

    # Duration badge
    dur_ms = duration.get("total_ms", 0) if duration else 0
    dur_html = (
        f'<span class="dur-badge">{_fmt_ms(dur_ms)}</span>'
        if dur_ms > 0 else ""
    )

    # Artifact panel (실패 TC만)
    artifact_html = ""
    if outcome == "failed" and artifacts:
        artifact_html = _build_artifact_panel(uid, duration, artifacts)

    return (
        f'<div class="case-item {status_cls}" data-status="{status_cls}" data-toggle="{uid}">'
        f'  <div class="case-header">'
        f'    <span class="case-dot {status_cls}"></span>'
        f'    <span class="case-title">{_esc(title)}</span>'
        f'    <div class="case-right">'
        f'      {dur_html}'
        f'      <span class="case-status-txt {status_cls}">{badge_txt}</span>'
        f'      <span class="chevron" id="chv_{uid}">&#8250;</span>'
        f'    </div>'
        f'  </div>'
        f'  <div class="case-detail" id="detail_{uid}">'
        f'    {skip_reason_html}'
        f'    {pre_html}'
        f'    <div class="detail-row">'
        f'      <span class="detail-label">실행 절차</span>'
        f'      <span class="detail-val"><ol class="steps-list">{steps_html}</ol></span>'
        f'    </div>'
        f'    <div class="detail-row">'
        f'      <span class="detail-label">기대 결과</span>'
        f'      <span class="detail-val">{exp_content}</span>'
        f'    </div>'
        f'    {artifact_html}'
        f'  </div>'
        f'</div>'
    )


def build_group_section(label: str, rows_html: str,
                        g_pass_cnt: int, g_total_cnt: int,
                        g_passed: bool, has_tests: bool,
                        g_skip_cnt: int = 0) -> str:
    """그룹 카드 HTML 생성. 접기/펼치기 + 필터 + 페이지네이션."""
    status_cls = "pass" if g_passed else ("fail" if has_tests else "warn")
    g_fail_cnt = g_total_cnt - g_pass_cnt - g_skip_cnt
    status_txt = "통과" if g_passed else ("실패" if has_tests else "미실행")
    if g_passed and g_skip_cnt > 0:
        status_txt = f"통과 · {g_skip_cnt}건 건너뜀"
    display_label = _esc(label)
    skip_btn = (
        f'<button class="fbtn skip" data-filter="{label}" data-filter-val="skip">'
        f'건너뜀 ({g_skip_cnt})</button>'
        if g_skip_cnt > 0 else ""
    )

    return f"""
<section class="group-card" id="group_{label}">
  <div class="group-header {status_cls}" data-toggle-group="{label}" style="cursor:pointer">
    <div class="group-title-wrap">
      <span class="group-chevron" id="gchv_{label}">&#9654;</span>
      <span class="group-dot {status_cls}"></span>
      <span class="group-title">{display_label}</span>
      <span class="group-sub">{g_pass_cnt} / {g_total_cnt - g_skip_cnt} 통과{f" · {g_skip_cnt}건 건너뜀" if g_skip_cnt else ""}</span>
    </div>
    <div class="group-right">
      <span class="badge {status_cls}">{status_txt}</span>
    </div>
  </div>
  <div class="group-body" id="gbody_{label}" style="display:none">
    <div class="filter-bar" id="fbar_{label}">
      <button class="fbtn active" data-filter="{label}" data-filter-val="all">전체 ({g_total_cnt})</button>
      <button class="fbtn pass" data-filter="{label}" data-filter-val="pass">통과 ({g_pass_cnt})</button>
      <button class="fbtn fail" data-filter="{label}" data-filter-val="fail">실패 ({g_fail_cnt})</button>
      {skip_btn}
      <span class="pager" id="pager_{label}"></span>
    </div>
    <div class="case-list" id="clist_{label}">{rows_html}</div>
  </div>
</section>"""


def report_css() -> str:
    return """
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
  :root {
    color-scheme:light;
    --bg:#F5F6F8;--surface:#FFFFFF;--surface2:#F0F2F5;--log-bg:#F8F9FB;
    --border:#E2E5EA;--border-input:#8B93A1;
    --text:#111827;--text2:#4B5563;--text3:#6B7280;
    --pass:#15803D;--pass-bg:#E6F4EA;--fail:#B91C1C;--fail-bg:#FDECEC;
    --warn:#92400E;--warn-bg:#FEF3C7;--skip:var(--text3);--skip-bg:var(--surface2);
    --accent:#1F4FD1;--accent-hover:#163A9C;--accent-bg:#E8EEFC;--on-accent:#FFFFFF;
    --radius:8px;--radius-sm:6px;--radius-badge:4px;
    --sans:'IBM Plex Sans KR',system-ui,sans-serif;--mono:'JetBrains Mono',ui-monospace,monospace;
    --scrim:rgb(17 24 39 / .45);--shadow:0 12px 32px rgb(17 24 39 / .18);
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:var(--sans);font-size:14px;background:var(--bg);color:var(--text);min-height:100vh}
  button,a{font:inherit}
  button:focus-visible,a:focus-visible,[data-toggle]:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  a{color:var(--accent)}a:hover{color:var(--accent-hover)}
  .report-header{background:var(--surface);border-bottom:1px solid var(--border)}
  .topbar{max-width:1240px;margin:auto;padding:20px 32px;display:flex;align-items:center;gap:16px}
  .topbar h1{font-size:22px;font-weight:600;line-height:1.4}
  .report-title{display:flex;align-items:center;gap:10px}
  .meta{font-size:13px;color:var(--text2);margin-top:6px}
  .layout{max-width:1240px;margin:auto;padding:24px 32px;display:grid;grid-template-columns:220px minmax(0,1fr);gap:24px;align-items:start}
  .sidebar{position:sticky;top:24px;max-height:calc(100vh - 48px);overflow:auto}
  .sidebar-logo{padding:0 12px 16px}
  .logo-text{font-size:15px;font-weight:600}.logo-sub{font-size:12px;color:var(--text3);margin-top:4px}
  .nav-label{font-size:12px;color:var(--text3);padding:0 12px 6px}
  .nav-item{font-size:13px;color:var(--text);padding:8px 12px;border-radius:var(--radius-sm);cursor:pointer;list-style:none;display:flex;align-items:center;gap:8px}
  .nav-item:hover{background:var(--surface2)}
  .nav-item.active{background:var(--accent-bg);color:var(--accent);font-weight:600}
  .nav-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
  .nav-dot.pass{background:var(--pass)}.nav-dot.fail{background:var(--fail)}.nav-dot.warn{background:var(--warn)}
  .nav-count{margin-left:auto;font-size:12px;color:var(--text3);font-family:var(--mono);white-space:nowrap}
  .main{min-width:0}
  .overall-badge,.badge{display:inline-block;font-size:12px;font-weight:600;padding:2px 8px;border-radius:var(--radius-badge);white-space:nowrap}
  .overall-badge.pass,.badge.pass{background:var(--pass-bg);color:var(--pass)}
  .overall-badge.fail,.badge.fail{background:var(--fail-bg);color:var(--fail)}
  .badge.warn{background:var(--warn-bg);color:var(--warn)}
  .stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));margin-bottom:20px;border:1px solid var(--border);border-radius:var(--radius);background:var(--surface);overflow:hidden}
  .stat-card{padding:16px 20px;display:flex;flex-direction:column;gap:6px}
  .stat-card+.stat-card{border-left:1px solid var(--border)}
  .stat-num{font-size:24px;font-weight:600;line-height:1.4;font-family:var(--mono);order:1}
  .stat-lbl{font-size:13px;color:var(--text2)}
  .group-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:20px;overflow:hidden}
  .group-header{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 16px}
  .group-title-wrap{display:flex;align-items:center;gap:10px;min-width:0;flex-wrap:wrap}
  .group-chevron{color:var(--text3);font-size:12px;display:inline-block;transition:transform .15s}
  .group-chevron.open{transform:rotate(90deg)}
  .group-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
  .group-dot.pass{background:var(--pass)}.group-dot.fail{background:var(--fail)}.group-dot.warn{background:var(--warn)}
  .group-title{font-size:15px;font-weight:600;font-family:var(--mono)}
  .group-sub{font-size:13px;color:var(--text2)}.group-right{display:flex;align-items:center;gap:8px}
  .filter-bar{display:flex;align-items:center;padding:10px 16px;border-top:1px solid var(--border);border-bottom:1px solid var(--border)}
  .fbtn{height:32px;padding:0 14px;border:1px solid var(--border);border-right:0;background:var(--surface);color:var(--text2);cursor:pointer;font-size:13px}
  .fbtn:first-child{border-radius:var(--radius-sm) 0 0 var(--radius-sm)}
  .fbtn:last-of-type{border-right:1px solid var(--border);border-radius:0 var(--radius-sm) var(--radius-sm) 0}
  .fbtn:hover{background:var(--surface2)}.fbtn.active{background:var(--text);color:var(--on-accent)}
  .pager{margin-left:auto;display:flex;align-items:center;gap:10px;font-size:13px;color:var(--text2);font-family:var(--mono)}
  .pager button{height:32px;padding:0 12px;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface);color:var(--text);cursor:pointer}
  .pager button:disabled{color:var(--text3);background:var(--surface2);cursor:default}
  .pager button:not(:disabled):hover{background:var(--accent-bg);color:var(--accent)}
  .case-item{border-bottom:1px solid var(--border);cursor:pointer}.case-item:last-child{border-bottom:none}
  .case-item:hover{background:var(--log-bg)}
  .case-header{display:flex;align-items:center;gap:12px;padding:14px 16px}
  .case-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
  .case-dot.pass{background:var(--pass)}.case-dot.fail{background:var(--fail)}.case-dot.skip{background:var(--skip)}
  .case-title{flex:1;min-width:0;font-size:14px;font-weight:600;line-height:1.5}
  .case-right{display:flex;align-items:center;gap:12px;flex-shrink:0}
  .case-status-txt{font-size:12px;font-weight:600;padding:2px 8px;border-radius:var(--radius-badge)}
  .case-status-txt.pass{color:var(--pass);background:var(--pass-bg)}
  .case-status-txt.fail{color:var(--fail);background:var(--fail-bg)}
  .case-status-txt.skip{color:var(--skip);background:var(--skip-bg)}
  .chevron{color:var(--text3);font-size:18px;display:inline-block;transition:transform .15s}.chevron.open{transform:rotate(90deg)}
  .case-detail{display:none;padding:0 16px 16px 34px}
  .detail-row{display:flex;gap:16px;margin-top:10px;font-size:13px;line-height:1.6}
  .detail-label{min-width:90px;font-weight:600;color:var(--text2);flex-shrink:0}
  .detail-val{color:var(--text2);overflow-wrap:anywhere}
  .steps-list{padding-left:16px}.steps-list li{margin:3px 0}
  .empty-msg{padding:16px;font-size:13px;color:var(--text3)}
  .dur-badge{font-size:12px;color:var(--text3);font-family:var(--mono);white-space:nowrap}
  .artifact-panel{margin-top:16px;background:var(--log-bg);border:1px solid var(--border);border-radius:var(--radius-sm);overflow:hidden}
  .artifact-sub{padding:14px 16px;border-bottom:1px solid var(--border)}.artifact-sub:last-child{border-bottom:none}
  .artifact-sub-title{font-size:13px;font-weight:600;color:var(--text2);margin-bottom:10px}
  .timing-list{display:flex;flex-direction:column;gap:1px}
  .timing-row{display:flex;align-items:center;justify-content:space-between;padding:5px 8px}.timing-row:hover{background:var(--surface2)}
  .timing-name,.timing-ms{font:12px var(--mono);color:var(--text2)}
  .timing-name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-right:12px}.timing-name.hooks{color:var(--text3)}
  .screenshot-wrap{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:8px}
  .screenshot-thumb{max-width:300px;max-height:220px;object-fit:cover;border-radius:var(--radius-sm);border:1px solid var(--border);cursor:zoom-in}
  .screenshot-thumb:hover{outline:2px solid var(--accent)}
  .trace-link{display:inline-flex;align-items:center;font-size:13px;text-decoration:none;padding:6px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface);cursor:pointer}
  .trace-link:hover{background:var(--accent-bg)}
  .artifact-video{max-width:100%;width:480px;border-radius:var(--radius-sm);border:1px solid var(--border);display:block;margin-bottom:8px;background:var(--text)}
  .artifact-dl{font-size:13px;text-decoration:none}
  .lb-overlay{display:none;position:fixed;inset:0;background:var(--scrim);z-index:9999;align-items:center;justify-content:center;cursor:zoom-out}
  .lb-overlay.open{display:flex}
  .lb-overlay img{max-width:92vw;max-height:92vh;object-fit:contain;border-radius:var(--radius);box-shadow:var(--shadow)}
  @media(max-width:800px){.layout{grid-template-columns:1fr;padding:20px}.sidebar{position:static;max-height:none}.topbar{padding:20px}.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.stat-card{border-bottom:1px solid var(--border)}.filter-bar{flex-wrap:wrap;gap:6px}.group-title-wrap{gap:6px}.case-header{gap:8px}.case-detail{padding-left:16px}.detail-row{flex-direction:column;gap:4px}}
"""


def report_js() -> str:
    return """
var _gState = {};
var PP = """ + str(CASES_PER_PAGE) + """;

function _gs(label) {
  if (!_gState[label]) _gState[label] = {filter:'all', page:1, open:false};
  return _gState[label];
}

function toggle(uid) {
  var d=document.getElementById('detail_'+uid);
  var c=document.getElementById('chv_'+uid);
  if(d.style.display==='none'||!d.style.display){d.style.display='block';c.classList.add('open');}
  else{d.style.display='none';c.classList.remove('open');}
}

function scrollToGroup(label) {
  var el=document.getElementById('group_'+label);
  if(el)el.scrollIntoView({behavior:'smooth',block:'start'});
}

var _selectedNav = 'all';

function selectNav(label) {
  document.querySelectorAll('.nav-item').forEach(function(el){el.classList.remove('active');});
  var navEl = document.getElementById('nav_'+label);
  if(navEl) navEl.classList.add('active');
  _selectedNav = label;
  var cards = document.querySelectorAll('.group-card');
  if(label === 'all') {
    cards.forEach(function(card){
      card.style.display = '';
      var gl = card.id.replace('group_','');
      var st = _gs(gl);
      if(st.open) toggleGroup(gl);
    });
  } else {
    cards.forEach(function(card){
      var gl = card.id.replace('group_','');
      if(gl === label) {
        card.style.display = '';
        var st = _gs(gl);
        if(!st.open) toggleGroup(gl);
        scrollToGroup(label);
      } else {
        card.style.display = 'none';
      }
    });
  }
}

function toggleGroup(label) {
  var st=_gs(label); st.open=!st.open;
  var body=document.getElementById('gbody_'+label);
  var chv=document.getElementById('gchv_'+label);
  if(st.open){body.style.display='block';chv.classList.add('open');applyFilter(label);}
  else{body.style.display='none';chv.classList.remove('open');}
}

function setFilter(label, f) {
  var st=_gs(label); st.filter=f; st.page=1;
  applyFilter(label);
}

function setPage(label, p) {
  var st=_gs(label); st.page=p;
  applyFilter(label);
}

function applyFilter(label) {
  var st=_gs(label);
  var list=document.getElementById('clist_'+label);
  var items=list.querySelectorAll('.case-item');
  var visible=[];
  items.forEach(function(el){
    if(st.filter==='all'||el.dataset.status===st.filter){visible.push(el);el.style.display='';}
    else{el.style.display='none';}
  });
  var total=visible.length;
  var pages=Math.max(1,Math.ceil(total/PP));
  st.page=Math.min(st.page,pages);
  var start=(st.page-1)*PP;
  visible.forEach(function(el,i){
    el.style.display=(i>=start&&i<start+PP)?'':'none';
  });
  var bar=document.getElementById('fbar_'+label);
  bar.querySelectorAll('.fbtn').forEach(function(btn){btn.classList.remove('active');});
  bar.querySelectorAll('.fbtn').forEach(function(btn){
    if(st.filter==='all'&&btn.textContent.startsWith('전체'))btn.classList.add('active');
    if(st.filter==='pass'&&btn.textContent.startsWith('통과'))btn.classList.add('active');
    if(st.filter==='fail'&&btn.textContent.startsWith('실패'))btn.classList.add('active');
    if(st.filter==='skip'&&btn.textContent.startsWith('건너뜀'))btn.classList.add('active');
  });
  var pg=document.getElementById('pager_'+label);
  if(pages>1){
    pg.innerHTML='<button data-page-group="'+label+'" data-page-dir="prev"'+(st.page<=1?' disabled':'')+'>\\u00ab</button>'
      +'<span>'+st.page+' / '+pages+'</span>'
      +'<button data-page-group="'+label+'" data-page-dir="next"'+(st.page>=pages?' disabled':'')+'>\\u00bb</button>';
  }else{pg.innerHTML='';}
}

// Lightbox
function _openLb(src) {
  var ov = document.getElementById('lb-overlay');
  if (!ov) return;
  document.getElementById('lb-img').src = src;
  ov.classList.add('open');
}

// Event delegation
document.addEventListener('click', function(e) {
  var t;
  // Lightbox close
  t = e.target.closest('#lb-overlay');
  if(t){t.classList.remove('open');return;}
  // Screenshot lightbox open
  t = e.target.closest('.screenshot-thumb');
  if(t){_openLb(t.src);return;}
  // Trace copy
  t = e.target.closest('.trace-link');
  if(t){
    var p = t.getAttribute('data-trace-path');
    var cmd = 'npx playwright show-trace ' + p;
    if(navigator.clipboard){
      navigator.clipboard.writeText(cmd).then(function(){
        t.innerHTML = '복사 완료';
        setTimeout(function(){t.innerHTML='trace 명령 복사';},1600);
      }).catch(function(){alert(cmd);});
    } else { alert(cmd); }
    return;
  }
  t = e.target.closest('[data-toggle]');
  if(t){toggle(t.getAttribute('data-toggle'));return;}
  t = e.target.closest('[data-toggle-group]');
  if(t){toggleGroup(t.getAttribute('data-toggle-group'));return;}
  t = e.target.closest('[data-filter]');
  if(t){setFilter(t.getAttribute('data-filter'),t.getAttribute('data-filter-val'));return;}
  t = e.target.closest('[data-nav]');
  if(t){selectNav(t.getAttribute('data-nav'));return;}
  t = e.target.closest('[data-page-group]');
  if(t&&!t.disabled){
    var gl=t.getAttribute('data-page-group');
    var st=_gs(gl);
    var dir=t.getAttribute('data-page-dir');
    setPage(gl, dir==='prev'?st.page-1:st.page+1);
  }
});

// Lightbox DOM 생성
(function(){
  var ov=document.createElement('div');
  ov.id='lb-overlay';ov.className='lb-overlay';
  var img=document.createElement('img');img.id='lb-img';
  ov.appendChild(img);
  if(document.body) document.body.appendChild(ov);
  else document.addEventListener('DOMContentLoaded',function(){document.body.appendChild(ov);});
})();
"""


def build_report(groups_data: list, summary: dict,
                 created_at: str, subtitle: str = "테스트 리포트") -> str:
    """완성 리포트 HTML 반환.

    groups_data: [{"label": str, "rows_html": str,
                   "pass_cnt": int, "total_cnt": int,
                   "all_pass": bool, "has_tests": bool,
                   "skip_cnt": int (optional)}, ...]
    """
    subtitle = {"Test Report": "단일 파이프라인", "Parallel Test Report": "병렬 파이프라인"}.get(subtitle, subtitle)
    pass_total = summary.get("passed", 0)
    fail_total = summary.get("failed", 0) + summary.get("error", 0)
    skip_total = summary.get("skipped", 0)
    total = pass_total + fail_total + skip_total
    pass_rate = round(pass_total / total * 100, 1) if total else 0
    all_pass = fail_total == 0
    overall_cls = "pass" if all_pass else "fail"
    overall_txt = "모두 통과" if all_pass else f"{fail_total}건 실패"

    nav_items = f'<li class="nav-item active" id="nav_all" data-nav="all">전체 ({total})</li>\n'
    for g in groups_data:
        lbl = g["label"]
        g_skip_cnt = g.get("skip_cnt", 0)
        g_non_skip = g["total_cnt"] - g_skip_cnt
        dot_cls = "pass" if g["all_pass"] else ("fail" if g["has_tests"] else "warn")
        skip_label = (
            f'<span style="font-size:12px;color:var(--skip);margin-left:3px;">· {g_skip_cnt}건 건너뜀</span>'
            if g_skip_cnt > 0 else ""
        )
        nav_items += (
            f'<li class="nav-item" id="nav_{lbl}" data-nav="{lbl}">'
            f'<span class="nav-dot {dot_cls}"></span>'
            f'{_esc(lbl)}'
            f'<span class="nav-count">{g["pass_cnt"]}/{g_non_skip}{skip_label}</span>'
            f'</li>\n'
        )

    group_sections = ""
    for g in groups_data:
        group_sections += build_group_section(
            g["label"], g["rows_html"],
            g["pass_cnt"], g["total_cnt"],
            g["all_pass"], g["has_tests"],
            g_skip_cnt=g.get("skip_cnt", 0),
        )

    n_groups = len(groups_data)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>테스트 리포트</title>
<style>{report_css()}</style>
</head>
<body>
<header class="report-header">
  <div class="topbar">
    <div>
      <div class="report-title"><h1>테스트 리포트</h1><div class="overall-badge {overall_cls}">{overall_txt}</div></div>
      <div class="meta">{created_at} &middot; {subtitle} &middot; 그룹 {n_groups}개 &middot; {total}건</div>
    </div>
  </div>
</header>
<div class="layout">
  <aside class="sidebar">
    <div class="sidebar-logo">
      <div class="logo-text">QA Native</div>
      <div class="logo-sub">{subtitle}</div>
    </div>
    <nav class="nav-section">
      <div class="nav-label">그룹</div>
      <ul style="list-style:none;">{nav_items}</ul>
    </nav>
  </aside>
  <div class="main">
    <div class="stats">
      <div class="stat-card"><div class="stat-num" style="color:var(--text);">{total}</div><div class="stat-lbl">전체</div></div>
      <div class="stat-card"><div class="stat-num" style="color:var(--pass);">{pass_total}</div><div class="stat-lbl">통과</div></div>
      <div class="stat-card"><div class="stat-num" style="color:var(--fail);">{fail_total}</div><div class="stat-lbl">실패</div></div>
      <div class="stat-card"><div class="stat-num" style="color:var(--skip);">{skip_total}</div><div class="stat-lbl">건너뜀</div></div>
      <div class="stat-card"><div class="stat-num" style="color:{'var(--pass)' if all_pass else 'var(--fail)'};">{pass_rate}%</div><div class="stat-lbl">통과율</div></div>
    </div>
    {group_sections}
  </div>
</div>
<script>{report_js()}</script>
</body>
</html>"""
