"""
jira_reporter.py — QA 테스트 실패 시 Jira 이슈 자동 생성

사용법:
    python scripts/jira_reporter.py                   # 최신 실패 결과 자동 감지
    python scripts/jira_reporter.py --group login     # 특정 그룹만
    python scripts/jira_reporter.py --dry-run         # 생성 없이 미리보기

설정:
    config/jira_config.json 에 인증 정보와 프로젝트 설정 저장.
    민감 정보는 환경변수 JIRA_TOKEN 으로도 지정 가능.
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# ── 경로 설정 ────────────────────────────────────────────────────────────────
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

CONFIG_PATH    = _PROJECT_ROOT / "config" / "jira_config.json"
PARALLEL_STATE  = _PROJECT_ROOT / "state" / "parallel.json"
SCREENSHOTS_DIR = _PROJECT_ROOT / "tests" / "screenshots"
VIDEOS_DIR      = _PROJECT_ROOT / "tests" / "videos"
TESTCASES_DIR   = _PROJECT_ROOT / "testcases"

# ── 기본 설정 ────────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "base_url":    "https://skj94268.atlassian.net",
    "email":       "skj94268@gmail.com",
    "token":       "",                  # 환경변수 JIRA_TOKEN 또는 여기에 직접 입력
    "project_key": "SCRUM",
    "issue_type_id": "10006",           # 버그(10006)
    "epic_key":    "SCRUM-5",           # QA 자동화 실패 이슈 트래킹 에픽
    "version":     "v1.0.0",
    "auto_attach": True,                # 스크린샷/영상 자동 첨부 여부
}


# ── TC 마크다운 파싱 ─────────────────────────────────────────────────────────

def _find_tc_md(group: str, test_name: str) -> Path | None:
    """테스트 함수명 → testcases/{group}/tc_{N}_*.md 매칭.

    test_name 예: test_tc_01_customer_login_empty_field_validation
    → testcases/customer_login/tc_01_*.md
    """
    import re as _re
    group_dir = TESTCASES_DIR / group
    if not group_dir.is_dir():
        return None

    # test_name에서 tc 번호 추출 (tc_01, tc_02 ...)
    m = _re.search(r"tc_(\d+)", test_name)
    if not m:
        return None
    tc_num = m.group(1)

    for md_file in sorted(group_dir.glob(f"tc_{tc_num}_*.md")):
        return md_file
    return None


def _parse_tc_md(md_path: Path) -> dict:
    """tc_*.md → {steps: [...], expected: [...], precondition: [...], title: str} 파싱."""
    import re as _re
    text = md_path.read_text(encoding="utf-8")

    # YAML frontmatter 제거
    body = _re.sub(r"^---.*?---\s*", "", text, flags=_re.DOTALL).strip()

    def _extract_section(section_name: str) -> list[str]:
        """## {section_name} 아래 항목 수집 (다음 ## 나오기 전까지)."""
        pattern = rf"##\s+{section_name}\s*\n(.*?)(?=\n##|\Z)"
        s = _re.search(pattern, body, _re.DOTALL | _re.IGNORECASE)
        if not s:
            return []
        lines = s.group(1).strip().splitlines()
        result = []
        for line in lines:
            line = line.strip()
            # 번호 목록(1. / 0.) 또는 불릿(- / *) 앞부분 제거
            cleaned = _re.sub(r"^(\d+\.|[-*])\s+", "", line)
            if cleaned:
                result.append(cleaned)
        return result

    # 제목 (# 로 시작하는 첫 줄)
    title_m = _re.search(r"^#\s+(.+)$", body, _re.MULTILINE)
    title = title_m.group(1).strip() if title_m else md_path.stem

    return {
        "title":        title,
        "precondition": _extract_section("Precondition"),
        "steps":        _extract_section("Steps"),
        "expected":     _extract_section("Expected"),
    }


# ── Jira API 클라이언트 ───────────────────────────────────────────────────────

class JiraClient:
    def __init__(self, cfg: dict):
        token = os.environ.get("JIRA_TOKEN") or cfg.get("token", "")
        if not token:
            raise ValueError("Jira API 토큰이 없습니다. config/jira_config.json의 token 필드 또는 JIRA_TOKEN 환경변수를 설정하세요.")
        creds = base64.b64encode(f"{cfg['email']}:{token}".encode()).decode()
        self._base = cfg["base_url"].rstrip("/") + "/rest/api/3"
        self._headers = {
            "Authorization": f"Basic {creds}",
            "Accept":        "application/json",
            "Content-Type":  "application/json",
        }

    def request(self, method: str, path: str, body=None) -> dict:
        url  = f"{self._base}{path}"
        data = json.dumps(body).encode() if body else None
        req  = urllib.request.Request(url, data=data, headers=self._headers, method=method)
        try:
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            err = e.read().decode()
            raise RuntimeError(f"Jira API {method} {path} → {e.code}: {err[:400]}")

    def attach_file(self, issue_key: str, file_path: Path) -> dict:
        """이슈에 파일 첨부 (multipart/form-data)."""
        if not file_path.exists():
            return {}
        mime, _ = mimetypes.guess_type(str(file_path))
        mime = mime or "application/octet-stream"

        boundary = "----JiraUpload7a3f"
        file_data = file_path.read_bytes()
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
            f"Content-Type: {mime}\r\n\r\n"
        ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()

        headers = dict(self._headers)
        headers.pop("Content-Type")
        headers["Content-Type"]    = f"multipart/form-data; boundary={boundary}"
        headers["X-Atlassian-Token"] = "no-check"

        url = f"{self._base}/issue/{issue_key}/attachments"
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            print(f"  ⚠️ 첨부 실패 ({file_path.name}): {e.code} {e.read().decode()[:200]}")
            return {}


# ── 이슈 생성 ────────────────────────────────────────────────────────────────

def _adf_text(text: str) -> dict:
    """단순 텍스트 → Atlassian Document Format 노드."""
    return {"type": "text", "text": text}


def _adf_para(*texts) -> dict:
    return {"type": "paragraph", "content": [_adf_text(t) for t in texts]}


def _adf_heading(text: str, level: int = 3) -> dict:
    return {
        "type": f"heading",
        "attrs": {"level": level},
        "content": [_adf_text(text)],
    }


def _adf_bullet(items: list[str]) -> dict:
    return {
        "type": "bulletList",
        "content": [
            {"type": "listItem", "content": [_adf_para(item)]}
            for item in items
        ],
    }


def _adf_ordered(items: list[str]) -> dict:
    return {
        "type": "orderedList",
        "content": [
            {"type": "listItem", "content": [_adf_para(item)]}
            for item in items
        ],
    }


def _build_description(failure: dict, cfg: dict) -> dict:
    """실패 정보 → Jira ADF description.

    재현 스텝/기대결과는 testcases/{group}/tc_{N}_*.md 에서 우선 로드.
    md 파일이 없을 때만 failure dict의 값으로 폴백.
    """
    test_name  = failure.get("test_name", "")
    group      = failure.get("group", "")
    url        = failure.get("url", "")
    error_msg  = failure.get("error_msg", "")
    repro_rate = failure.get("repro_rate", "Always")
    executed_at = failure.get("executed_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # ── tc_*.md 에서 실제 스텝/기대결과 로드 ──────────────────────────
    tc_data: dict = {}
    md_path = _find_tc_md(group, test_name)
    if md_path:
        try:
            tc_data = _parse_tc_md(md_path)
        except Exception:
            pass

    precondition = tc_data.get("precondition") or []
    steps        = tc_data.get("steps")        or failure.get("steps", [f"{url} 접속", "로그인 버튼 클릭", "결과 확인"])
    expected_list = tc_data.get("expected")    or []
    expected_str  = "\n".join(expected_list) if expected_list else failure.get("expected", "테스트가 정상적으로 통과해야 한다.")

    content = [
        _adf_heading("📋 기본 정보", 2),
        _adf_bullet([
            f"테스트 그룹: {group}",
            f"테스트 함수: {test_name}",
            f"대상 URL: {url}",
            f"실행 시각: {executed_at}",
            f"재현 상태: {repro_rate}",
        ]),
    ]

    if precondition:
        content += [
            _adf_heading("⚙️ 사전 조건", 2),
            _adf_ordered(precondition),
        ]

    content += [
        _adf_heading("🔁 재현 스텝", 2),
        _adf_ordered(steps),

        _adf_heading("✅ 기대 결과", 2),
        _adf_bullet(expected_list) if expected_list else _adf_para(expected_str),

        _adf_heading("❌ 실제 결과 (오류)", 2),
    ]

    if error_msg:
        content.append({
            "type": "codeBlock",
            "attrs": {"language": "text"},
            "content": [_adf_text(error_msg[:2000])],
        })
    else:
        content.append(_adf_para("스크린샷/영상 첨부파일 참조"))

    content += [
        _adf_heading("🔗 환경", 2),
        _adf_bullet([
            f"파이프라인: QA 자동화 (Playwright + pytest)",
            f"버전: {cfg.get('version', 'v1.0.0')}",
            f"스크린샷/영상: 첨부파일 참조",
            f"TC 파일: testcases/{group}/{md_path.name if md_path else '—'}",
        ]),
    ]

    return {"type": "doc", "version": 1, "content": content}


def create_jira_issue(client: JiraClient, cfg: dict, failure: dict, dry_run: bool = False) -> str | None:
    """실패 TC 1건 → Jira 이슈 생성 + 첨부파일 업로드."""
    group     = failure.get("group", "unknown")
    test_name = failure.get("test_name", "unknown")

    # 제목 = md 파일의 실제 TC 이름 우선, 없으면 함수명 폴백
    _md = _find_tc_md(group, test_name)
    _tc_title = ""
    if _md:
        try:
            _tc_title = _parse_tc_md(_md).get("title", "")
        except Exception:
            pass
    summary = f"[QA 실패] {_tc_title or test_name}"

    description = _build_description(failure, cfg)

    issue_body: dict = {
        "fields": {
            "project":     {"key": cfg["project_key"]},
            "issuetype":   {"id":  cfg["issue_type_id"]},
            "summary":     summary,
            "description": description,
        }
    }

    # 버전(Affects Version) — 필드 지원 여부에 따라 선택 적용
    if cfg.get("version"):
        issue_body["fields"]["versions"] = [{"name": cfg["version"]}]

    epic_key = cfg.get("epic_key", "")

    if dry_run:
        print(f"\n[DRY-RUN] 생성 예정 이슈:")
        print(f"  Summary : {summary}")
        print(f"  Type    : {cfg['issue_type_id']}")
        print(f"  Version : {cfg.get('version','')}")
        print(f"  상위(에픽): {epic_key} (하위 이슈로 생성)")
        screenshot = failure.get("screenshot_path", "")
        video      = failure.get("video_path", "")
        if screenshot:
            print(f"  스크린샷: {screenshot}")
        if video:
            print(f"  영상    : {video}")
        return None

    # 에픽 하위 이슈로 생성 — parent 필드 (next-gen/team-managed)
    # 실패 시 customfield_10014 (classic) 으로 폴백
    if epic_key:
        issue_body["fields"]["parent"] = {"key": epic_key}

    try:
        result = client.request("POST", "/issue", issue_body)
    except RuntimeError as e:
        err_str = str(e)
        if "parent" in err_str or "customfield" in err_str:
            # parent 필드 지원 안 될 때 → customfield_10014 로 교체
            issue_body["fields"].pop("parent", None)
            issue_body["fields"]["customfield_10014"] = epic_key
            try:
                result = client.request("POST", "/issue", issue_body)
            except RuntimeError as e2:
                # 그것도 안 되면 에픽 연결 없이 생성
                issue_body["fields"].pop("customfield_10014", None)
                result = client.request("POST", "/issue", issue_body)
        else:
            raise

    issue_key = result.get("key", "")
    if not issue_key:
        print(f"  ❌ 이슈 생성 실패: {result}")
        return None

    issue_url = f"{cfg['base_url']}/browse/{issue_key}"
    print(f"  ✅ {issue_key} 생성 — {issue_url} (에픽 {epic_key} 하위)")

    # 첨부파일 업로드
    if cfg.get("auto_attach", True):
        screenshot = failure.get("screenshot_path", "")
        video      = failure.get("video_path", "")
        if screenshot and Path(screenshot).exists():
            client.attach_file(issue_key, Path(screenshot))
            print(f"     📷 스크린샷 첨부 완료")
        if video and Path(video).exists():
            client.attach_file(issue_key, Path(video))
            print(f"     🎥 영상 첨부 완료")

    return issue_key


# ── 실패 정보 추출 ────────────────────────────────────────────────────────────

def _scan_meta_files(group_filter: list[str] | None = None) -> list[dict]:
    """tests/screenshots/*.meta.json 에서 실패 TC 정보 수집."""
    failures = []
    if not SCREENSHOTS_DIR.exists():
        return failures

    for meta_file in sorted(SCREENSHOTS_DIR.glob("*.meta.json")):
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        group = meta.get("group", "")
        if group_filter and group not in group_filter:
            continue

        # 영상 경로 보완 (meta.json에 없을 때 규칙 기반 추론)
        video_path = meta.get("video_path", "")
        if not video_path:
            test_name = meta.get("test_name", "")
            candidate = VIDEOS_DIR / f"{group}__{test_name}.mp4"
            if candidate.exists():
                video_path = str(candidate)

        failures.append({
            "group":           group,
            "test_name":       meta.get("test_name", ""),
            "url":             meta.get("url", ""),
            "screenshot_path": meta.get("screenshot_path", ""),
            "trace_path":      meta.get("trace_path", ""),
            "video_path":      video_path,
            "error_msg":       "",   # conftest는 traceback을 meta에 저장 안 함 — 후속 개선 가능
            "executed_at":     meta.get("timestamp", "")[:19].replace("T", " "),
            "repro_rate":      "Always",
        })
    return failures


def _load_failures_from_state(group_filter: list[str] | None) -> list[dict]:
    """state/parallel.json 실패 목록 + meta.json 조합."""
    # meta.json 기반이 가장 신뢰성 있음 (conftest가 실패 시 즉시 저장)
    return _scan_meta_files(group_filter)


# ── 메인 ─────────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            cfg.update(saved)
        except Exception:
            pass
    # 토큰 환경변수 우선
    cfg["token"] = os.environ.get("JIRA_TOKEN") or cfg.get("token", "")
    return cfg


def _save_config(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    # 토큰은 파일에 저장 (환경변수 없을 때 fallback)
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="QA 실패 → Jira 이슈 자동 생성")
    parser.add_argument("--group", "-g", nargs="*", help="특정 그룹만 (예: --group login checkout)")
    parser.add_argument("--dry-run", action="store_true", help="실제 생성 없이 미리보기")
    parser.add_argument("--all", action="store_true", help="이미 생성된 이슈도 재생성")
    args = parser.parse_args()

    cfg = _load_config()
    if not cfg.get("token"):
        print("❌ Jira 토큰이 없습니다.")
        print("   config/jira_config.json의 token 필드를 채우거나")
        print("   export JIRA_TOKEN=<토큰> 후 재실행하세요.")
        sys.exit(1)

    failures = _load_failures_from_state(args.group)
    if not failures:
        print("✅ 실패한 TC가 없습니다. (tests/screenshots/ 에 meta.json 없음)")
        sys.exit(0)

    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Jira 이슈 생성 시작 — {len(failures)}건")
    print(f"  프로젝트 : {cfg['project_key']}")
    print(f"  에픽     : {cfg.get('epic_key','')}")
    print(f"  버전     : {cfg.get('version','')}")
    print()

    client = JiraClient(cfg)
    created = []
    for f in failures:
        print(f"[{f['group']}] {f['test_name']}")
        key = create_jira_issue(client, cfg, f, dry_run=args.dry_run)
        if key:
            created.append(key)

    if not args.dry_run:
        print(f"\n총 {len(created)}/{len(failures)}건 생성 완료")
        for k in created:
            print(f"  → {cfg['base_url']}/browse/{k}")

    # 설정 저장 (최초 실행 시)
    if not CONFIG_PATH.exists():
        _save_config(cfg)
        print(f"\n설정 저장: {CONFIG_PATH}")


if __name__ == "__main__":
    main()
