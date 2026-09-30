# TC Authoring Studio Phase 3 Implementation Plan — Confluence · Figma · PRD URL · 출처 버전 추적

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 생성 소스에 공개 PRD URL·Confluence 페이지·Figma 프레임을 더하고, 출처 문서가 바뀌면 관련 케이스를 "재검토 필요"로 표시해 차이를 보고 확인할 수 있게 한다.

**Architecture:** 모든 원격 요청은 SSRF 방어가 들어간 `_tc_fetch.fetch()` 하나를 거친다. 원문은 `_tc_html`(표준 라이브러리 html.parser)로 markdown이 되고, `_tc_connectors`가 Phase 2 소스 번들에 버전 포함 출처(`conf:48213377@v14`)로 넣는다. `_tc_source_watch`는 사용자가 요청할 때만 원격 버전을 확인해 케이스에 `flags.source_change`를 단다. 화면은 Phase 2의 `registerSourceTab()`에 탭 3개를 붙이는 `connectors.js`와, 라이브러리·상세·검토 화면의 작은 연결부로 이루어진다.

**Tech Stack:** Python 3.14 표준 라이브러리(urllib, html.parser, ipaddress, difflib), Confluence REST (Cloud v2 · Server/DC v1), Figma REST v1, 바닐라 JS, pytest + Playwright

**Spec:** [PRD](../../../design/tc-studio/TC_AUTHORING_PRD.md) F1.3·F1.4·F5.9·§7 · [명세](../../../design/tc-studio/TC_AUTHORING_ELEMENT_SPEC.md) 3.1·2.6장 · [목업](../../../../design-previews/tc-authoring-studio.html) 2번 화면 소스 탭·1번 화면 배너 · [로드맵](../TC_AUTHORING_ROADMAP.md) · 선행: [Phase 2 계획](2026-09-30-tc-authoring-phase2.md) 완료

> **검증 상태 (2026-09-30):** Phase 2까지 적용한 저장소 사본에 이 계획을 그대로 적용해 새 테스트 22개(단위·API 18 + E2E 4)를 포함한 `tests/unit/tc_library` 99개와 전체 775개가 통과했다. 원격 서비스는 녹화 응답(`fake_web` 픽스처)으로 검증했고 **실제 Confluence·Figma 계정으로는 확인하지 않았다.** 그래서 W11에 실제 계정 확인 절차를 넣었다.

## Global Constraints

- 원격 요청은 반드시 `_tc_fetch.fetch()`만 쓴다. `urllib`·`requests`를 직접 부르지 않는다.
- SSRF (PRD §7): https만 허용(설정한 DC base가 http면 그 호스트만 예외), 호스트 허용 목록, DNS 결과가 사설·루프백·링크로컬·예약 대역이면 거부(설정에서 `allow_private`를 켠 DC 호스트만 예외), 리다이렉트 자동 추적 금지·최대 3회 재검사, 15초, 응답 20MB(이미지 10MB).
- 사용자가 준 URL은 **id를 뽑는 데만** 쓴다. Confluence API 주소는 설정한 base로, Figma는 `https://api.figma.com`으로 서버가 조립한다. Confluence URL 호스트가 설정 base와 다르면 거부한다.
- 자격증명은 `config/confluence_config.json`, `config/figma_config.json`(gitignore) + 환경변수 우선(`CONFLUENCE_BASE_URL` `CONFLUENCE_EMAIL` `CONFLUENCE_TOKEN` `FIGMA_TOKEN`). 어떤 응답·화면에도 토큰을 내보내지 않는다. 빈 토큰으로 저장하면 기존 토큰을 유지한다.
- 출처 ref는 버전을 포함한다: `url:{sha12}` · `conf:{page_id}@v{n}` · `figma:{file_key}/{node_id|file}@{version}` (+ 섹션 `#§N`).
- Figma TEXT에서 온 화면 문구는 `verified: true`(확인)다. 나머지 출처는 계속 `false`(추정).
- 원격 버전 확인은 사용자가 "출처 변경 확인"을 누를 때만 한다 (라이브러리를 열 때마다 부르지 않는다).
- 새 의존성 없음 (HTML 변환도 표준 라이브러리).
- 커밋 메시지 끝: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Phase 3 결정

| # | 결정 | 이유 |
|---|---|---|
| X1 | Confluence·Figma는 MCP가 아니라 서버의 REST 호출로 가져온다 (PRD D3 유지) | 생성 세션에 도구를 주지 않는 Phase 2 결정 Y1과 맞물린다 |
| X2 | 재검토 표시는 상태(`status`)가 아니라 별도 `flags.source_change` | 원래 상태를 잃지 않는다 (명세 피드백 #7) |
| X3 | "변경 확인 완료"는 출처 ref의 버전만 새 값으로 바꾸고 표시를 지운다. rev는 올리지 않는다 | 내용이 바뀐 게 아니다. 내용 수정은 사람이 따로 한다 |
| X4 | 차이 보기는 번들에 남은 옛 본문과 현재 원격 본문의 줄 단위 비교. 옛 본문이 없으면(엑셀에서 온 출처 등) 새 본문만 보여 준다 | 옛 버전 원문을 원격에서 다시 받지 않는다 |
| X5 | HTML → markdown은 `html.parser` 자체 구현 (markdownify·bs4를 쓰지 않음) | 의존성을 늘리지 않는다. 표·목록·매크로·첨부만 다루면 된다 |
| X6 | Figma 프레임 이미지는 번들 `assets/`에 PNG로 저장해 검토 화면에만 보여 준다. 생성 세션에는 넘기지 않는다 | 생성 세션은 도구가 없다 (Y1). 텍스트 outline만으로 문구·컴포넌트·이동을 전달한다 |
| X7 | 연결 설정 창은 새로 생성 화면의 "연결 설정" 버튼으로 연다. Confluence·Figma 탭에서 미연결 상태로 수집하면 자동으로 연다 | 목업 흐름 |

---

## File Structure

| 파일 | 책임 | 작업 |
|---|---|---|
| `scripts/_tc_fetch.py` | 안전한 GET (`Policy`, `fetch`, `host_allowed`, 교체 가능한 `transport`·`resolver`) | C1 |
| `scripts/_tc_html.py` | HTML·Confluence storage → markdown, `<title>` | C1 |
| `scripts/_tc_credentials.py` | 자격증명 읽기·저장·마스킹·인증 헤더 | C2 |
| `.gitignore` | 자격증명 파일 2개 | C2 |
| `scripts/_tc_sources.py`, `_tc_generate.py` (수정) | 원격 소스 추가(`add_fetched`), 이미지 자산, ref로 소스 찾기 / Figma 문구 = 확인 | C3 |
| `scripts/_tc_connectors.py` | PRD URL · Confluence(Cloud·DC, 하위 페이지, 짧은 링크, 제목 주소) · Figma(프레임 outline·이미지) · 현재 버전·본문 다시 받기 | C3 |
| `scripts/_tc_model.py`, `_tc_library.py` (수정) | `flags` 필드, `needs_review` 필터, `set_flag`, `replace_source_version` | C4 |
| `scripts/_tc_source_watch.py` | 변경 확인(scan)·표시 목록·확인 완료(ack)·차이(diff) | C4 |
| `agents/dashboard/routes_tc_connectors.py` (+ `routes_tc_library.py`, `serve.py` 수정) | 자격증명·원격 소스·자산·출처 변경 API | C5 |
| `agents/dashboard/static/js/tc-studio/connectors.js` (+ `api.js`, `generate.js`, `review.js` 수정) | 원격 소스 탭 3개·연결 설정 창·Figma 프레임 | W9 |
| `state.js`, `library.js`, `detail.js` (수정) | 재검토 필터·배너·"출처 변경 확인"·차이·확인 완료 | W10 |
| `tests/unit/tc_library/…` | `fake_web` 픽스처, 녹화 응답, 테스트 | 전 작업 |

---

## Task C1: 안전한 수집기 + HTML 변환

**Files:**
- Create: `scripts/_tc_fetch.py`, `scripts/_tc_html.py`
- Modify: `tests/unit/tc_library/conftest.py` (`fake_web` 픽스처)
- Test: `tests/unit/tc_library/test_tc_fetch.py`

**Interfaces:**
- Produces:
  - `FetchError(LibraryError)` · `Response{status, headers(소문자 키), body, url; json(), text()}` · `Policy{hosts, private_hosts=(), http_hosts=(), max_bytes=20MB, headers={}}`
  - `host_allowed(host, patterns)` — `"*"`(모든 공개 호스트), `"*.atlassian.net"`(하위 도메인만), 정확히 일치
  - `fetch(url, policy) -> Response` — 오류 코드: `URL_NOT_ALLOWED HOST_NOT_ALLOWED DNS_FAILED PRIVATE_ADDRESS FETCH_FAILED RESPONSE_TOO_LARGE(413) AUTH_FAILED(502) NOT_FOUND_REMOTE(404) REMOTE_ERROR(502) TOO_MANY_REDIRECTS(502)`
  - 모듈 전역 `transport(url, headers, max_bytes) -> Response`, `resolver(host) -> [ip]` — 테스트가 바꾼다
  - `to_markdown(html) -> str`, `html_title(html) -> str`
  - 테스트 픽스처 `fake_web`: `web.add(url, body|json=, status=, headers=)`(끝이 `*`면 접두 일치), `web.private`(사설 IP로 풀릴 호스트), `web.calls`(보낸 요청과 헤더). `_paths.PROJECT_ROOT`를 임시 폴더로 바꾸고 자격증명 환경변수를 지운다.

- [ ] **Step 1: 픽스처 추가** — `tests/unit/tc_library/conftest.py` 끝에:

```python
@pytest.fixture
def fake_web(monkeypatch, tmp_path):
    """네트워크 없이 원격 응답을 흉내 낸다. web.add(url, body|json=…, status=, headers=)로 등록.
    url 끝이 '*'이면 접두 일치. web.private에 넣은 호스트는 사설 IP(10.0.0.5)로 풀린다."""
    import json as _json
    from types import SimpleNamespace

    import _paths
    import _tc_fetch

    web = SimpleNamespace(routes={}, calls=[], private=set())

    def add(url, body=b"", *, json=None, status=200, headers=None):
        if json is not None:
            body = _json.dumps(json, ensure_ascii=False).encode("utf-8")
            headers = {"content-type": "application/json", **(headers or {})}
        if isinstance(body, str):
            body = body.encode("utf-8")
        web.routes[url] = (status, {k.lower(): v for k, v in (headers or {}).items()}, body)

    def transport(url, headers, max_bytes):
        web.calls.append((url, dict(headers)))
        route = web.routes.get(url) or next(
            (v for k, v in web.routes.items() if k.endswith("*") and url.startswith(k[:-1])), None)
        if route is None:
            raise OSError(f"no fake route: {url}")
        status, hdrs, body = route
        return _tc_fetch.Response(status, hdrs, body[: max_bytes + 1], url)

    web.add = add
    monkeypatch.setattr(_tc_fetch, "transport", transport)
    monkeypatch.setattr(_tc_fetch, "resolver", lambda host: ["10.0.0.5"] if host in web.private else ["93.184.216.34"])
    for name in ("CONFLUENCE_BASE_URL", "CONFLUENCE_EMAIL", "CONFLUENCE_TOKEN", "FIGMA_TOKEN"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(_paths, "PROJECT_ROOT", tmp_path / "project_root")
    return web
```

- [ ] **Step 2: 실패하는 테스트 작성** — `tests/unit/tc_library/test_tc_fetch.py`

```python
from __future__ import annotations

import pytest

from _tc_fetch import FetchError, Policy, fetch, host_allowed
from _tc_html import html_title, to_markdown


def test_host_patterns():
    assert host_allowed("yafit.atlassian.net", ("*.atlassian.net",))
    assert not host_allowed("atlassian.net", ("*.atlassian.net",))
    assert not host_allowed("evil-atlassian.net", ("*.atlassian.net",))
    assert host_allowed("anything.example", ("*",))


def test_ssrf_defenses(fake_web):
    fake_web.add("https://docs.example.com/prd", "<p>ok</p>")
    assert fetch("https://docs.example.com/prd", Policy(hosts=("*",))).text() == "<p>ok</p>"

    cases = [
        ("http://docs.example.com/prd", Policy(hosts=("*",)), "URL_NOT_ALLOWED"),
        ("https://user:pw@docs.example.com/prd", Policy(hosts=("*",)), "URL_NOT_ALLOWED"),
        ("https://other.example.com/x", Policy(hosts=("docs.example.com",)), "HOST_NOT_ALLOWED"),
        ("file:///etc/passwd", Policy(hosts=("*",)), "URL_NOT_ALLOWED"),
    ]
    for url, policy, code in cases:
        with pytest.raises(FetchError) as exc:
            fetch(url, policy)
        assert exc.value.code == code, url

    fake_web.private.add("intranet.example.com")
    fake_web.add("https://intranet.example.com/x", "secret")
    with pytest.raises(FetchError) as exc:
        fetch("https://intranet.example.com/x", Policy(hosts=("*",)))
    assert exc.value.code == "PRIVATE_ADDRESS"
    assert fetch("https://intranet.example.com/x",
                 Policy(hosts=("intranet.example.com",), private_hosts=("intranet.example.com",))).text() == "secret"


def test_redirects_are_rechecked_and_limited(fake_web):
    fake_web.private.add("169.254.169.254")
    fake_web.add("https://docs.example.com/a", status=302, headers={"Location": "https://docs.example.com/b"})
    fake_web.add("https://docs.example.com/b", "final")
    fake_web.add("https://docs.example.com/meta", status=302, headers={"Location": "https://169.254.169.254/latest"})
    fake_web.add("https://docs.example.com/loop", status=302, headers={"Location": "/loop"})
    policy = Policy(hosts=("*",))

    resp = fetch("https://docs.example.com/a", policy)
    assert (resp.text(), resp.url) == ("final", "https://docs.example.com/b")
    with pytest.raises(FetchError) as exc:
        fetch("https://docs.example.com/meta", policy)
    assert exc.value.code == "PRIVATE_ADDRESS"
    with pytest.raises(FetchError) as exc:
        fetch("https://docs.example.com/loop", policy)
    assert exc.value.code == "TOO_MANY_REDIRECTS"


def test_size_cap_and_status_mapping(fake_web):
    fake_web.add("https://docs.example.com/big", b"x" * 2048)
    fake_web.add("https://docs.example.com/401", status=401)
    fake_web.add("https://docs.example.com/404", status=404)
    with pytest.raises(FetchError) as exc:
        fetch("https://docs.example.com/big", Policy(hosts=("*",), max_bytes=1024))
    assert exc.value.code == "RESPONSE_TOO_LARGE"
    for path, code in (("401", "AUTH_FAILED"), ("404", "NOT_FOUND_REMOTE")):
        with pytest.raises(FetchError) as exc:
            fetch(f"https://docs.example.com/{path}", Policy(hosts=("*",)))
        assert exc.value.code == code


def test_html_and_storage_to_markdown():
    html = ('<html><head><title>PRD 8.6</title><script>x()</script></head><body><nav>메뉴</nav>'
            '<h2>조건</h2><p>a<br>b</p><table><tr><th>조건</th><th>결과</th></tr><tr><td>1개</td><td>숨김 | 표시</td></tr></table>'
            '<ul><li>하나</li><li>둘<ol><li>셋</li></ol></li></ul>'
            '<ac:structured-macro ac:name="warning"><ac:parameter ac:name="title">t</ac:parameter>'
            '<ac:rich-text-body><p>주의 문구</p></ac:rich-text-body></ac:structured-macro>'
            '<ac:image><ri:attachment ri:filename="banner.png"/></ac:image></body></html>')
    md = to_markdown(html)
    assert html_title(html) == "PRD 8.6"
    assert "메뉴" not in md and "x()" not in md
    assert "## 조건\n\na\nb" in md
    assert "| 조건 | 결과 |\n|---|---|\n| 1개 | 숨김 \\| 표시 |" in md
    assert "- 하나\n- 둘\n  1. 셋" in md
    assert "> [주의]\n\n주의 문구" in md and "[이미지: banner.png]" in md
```

- [ ] **Step 3: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_fetch.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named '_tc_fetch'`

- [ ] **Step 4: 수집기** — `scripts/_tc_fetch.py`

```python
"""외부 문서 수집용 안전한 HTTP GET (PRD §7 SSRF, 로드맵 C1).

규칙:
- https만 허용한다. 예외: 사용자가 설정한 Confluence Server/DC base가 http이면 그 호스트만 http 허용.
- 호스트는 허용 목록과 맞아야 한다 ("*.atlassian.net"처럼 앞자리 와일드카드 1개 지원).
- DNS로 풀린 주소가 사설·루프백·링크로컬·예약 대역이면 거부한다.
  예외: allow_private=True로 명시한 호스트(사내 Confluence DC)만.
- 리다이렉트는 자동으로 따라가지 않는다. 최대 3번, 매번 위 검사를 다시 한다.
- 시간 제한 15초, 응답 크기 상한(기본 20MB). 넘으면 읽기를 멈추고 거부한다.

테스트는 모듈 전역 `transport`와 `resolver`를 바꿔 네트워크 없이 검증한다.
"""
from __future__ import annotations

import ipaddress
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from _tc_library import LibraryError

TIMEOUT = 15
MAX_BYTES = 20 * 1024 * 1024
MAX_REDIRECTS = 3


class FetchError(LibraryError):
    pass


@dataclass
class Response:
    status: int
    headers: dict[str, str]
    body: bytes
    url: str

    def json(self):
        import json
        return json.loads(self.body.decode("utf-8"))

    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


@dataclass
class Policy:
    """hosts: 허용 호스트 패턴. private_hosts: 사설 주소를 허용할 호스트(설정한 DC base). http_hosts: http 허용."""
    hosts: tuple[str, ...]
    private_hosts: tuple[str, ...] = ()
    http_hosts: tuple[str, ...] = ()
    max_bytes: int = MAX_BYTES
    headers: dict[str, str] = field(default_factory=dict)


def host_allowed(host: str, patterns: tuple[str, ...]) -> bool:
    host = host.lower().rstrip(".")
    for pattern in patterns:
        pattern = pattern.lower()
        if pattern == "*":                      # 공개 문서 URL: 호스트는 자유, 내부망 검사는 그대로
            return True
        if pattern.startswith("*."):
            if host.endswith(pattern[1:]) and host != pattern[2:]:
                return True
        elif host == pattern:
            return True
    return False


def _resolve(host: str) -> list[str]:
    return sorted({info[4][0] for info in socket.getaddrinfo(host, None)})


resolver = _resolve


def _check(url: str, policy: Policy) -> None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("https", "http") or not host:
        raise FetchError(f"지원하지 않는 주소입니다: {url}", "URL_NOT_ALLOWED")
    if parsed.scheme == "http" and host not in policy.http_hosts:
        raise FetchError("https 주소만 가져올 수 있습니다", "URL_NOT_ALLOWED")
    if parsed.username or parsed.password:
        raise FetchError("주소에 계정 정보를 넣을 수 없습니다", "URL_NOT_ALLOWED")
    if not host_allowed(host, policy.hosts):
        raise FetchError(f"허용되지 않은 호스트입니다: {host}", "HOST_NOT_ALLOWED")
    try:
        addresses = resolver(host)
    except OSError as exc:
        raise FetchError(f"주소를 찾을 수 없습니다: {host}", "DNS_FAILED") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address.split("%")[0])
        risky = ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved \
            or ip.is_multicast or ip.is_unspecified
        if risky and host not in policy.private_hosts:
            raise FetchError(f"내부망 주소로는 요청할 수 없습니다: {host} → {address}", "PRIVATE_ADDRESS")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # 리다이렉트는 fetch()가 직접 검사하며 따라간다
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def _urlopen(url: str, headers: dict[str, str], max_bytes: int) -> Response:
    request = urllib.request.Request(url, headers={"User-Agent": "qa-native-tc-studio/1", **headers})
    try:
        resp = _opener.open(request, timeout=TIMEOUT)
    except urllib.error.HTTPError as err:          # 3xx·4xx·5xx도 응답으로 돌려준다
        resp = err
    with resp:
        body = resp.read(max_bytes + 1)
        return Response(resp.status if hasattr(resp, "status") else resp.code,
                        {k.lower(): v for k, v in resp.headers.items()}, body, url)


transport = _urlopen


def fetch(url: str, policy: Policy) -> Response:
    """GET 1회. 2xx가 아니면 FetchError. 리다이렉트는 검사하며 최대 3번 따라간다."""
    for _ in range(MAX_REDIRECTS + 1):
        _check(url, policy)
        try:
            resp = transport(url, policy.headers, policy.max_bytes)
        except (OSError, TimeoutError) as exc:
            raise FetchError(f"요청에 실패했습니다: {exc}", "FETCH_FAILED") from exc
        if len(resp.body) > policy.max_bytes:
            raise FetchError(f"응답이 {policy.max_bytes // (1024 * 1024)}MB를 넘습니다", "RESPONSE_TOO_LARGE", 413)
        if resp.status in (301, 302, 303, 307, 308) and resp.headers.get("location"):
            url = urljoin(url, resp.headers["location"])
            continue
        if resp.status in (401, 403):
            raise FetchError("인증에 실패했습니다. 연결 설정의 토큰과 권한을 확인하세요", "AUTH_FAILED", 502)
        if resp.status == 404:
            raise FetchError("문서를 찾을 수 없습니다", "NOT_FOUND_REMOTE", 404)
        if not 200 <= resp.status < 300:
            raise FetchError(f"원격 서버 응답 {resp.status}", "REMOTE_ERROR", 502)
        return resp
    raise FetchError("리다이렉트가 너무 많습니다", "TOO_MANY_REDIRECTS", 502)
```

- [ ] **Step 5: HTML 변환** — `scripts/_tc_html.py`

```python
"""HTML·Confluence storage 포맷 → markdown (표준 라이브러리 html.parser만 사용).

지원: h1~h6(→ #~###), p·br, ul/ol·li, table(→ markdown 표, 셀 안 줄바꿈은 공백), pre·code,
Confluence 매크로(info·note·warning·panel·expand·code의 본문은 살리고 제목을 붙인다),
ac:image + ri:attachment(→ "[이미지: 파일명]"), ac:link + ri:page(→ 페이지 제목 텍스트).
script·style·nav·header·footer·ac:parameter는 버린다.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

_BLOCK = {"p", "div", "section", "article", "blockquote", "br", "hr"}
_SKIP = {"script", "style", "nav", "header", "footer", "noscript", "ac:parameter", "svg"}
_MACRO_TITLE = {"info": "정보", "note": "참고", "warning": "주의", "tip": "팁", "panel": "패널",
                "expand": "펼치기", "code": "코드"}


class _Converter(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[tuple[str, str, str]] = []   # (앞 구분자, 텍스트, 종류 block|list)
        self.line: list[str] = []
        self.next_sep = "\n\n"
        self.skip = 0
        self.lists: list[list] = []          # [kind, counter]
        self.table: list[list[str]] | None = None
        self.cell: list[str] | None = None
        self.heading = 0
        self.pre = False

    # ── 줄 관리 ──
    def _flush(self) -> None:
        text = re.sub(r"[ \t]+", " ", "".join(self.line)).strip() if not self.pre else "".join(self.line)
        self.line = []
        if not text:
            return
        sep, self.next_sep = self.next_sep, "\n\n"
        if self.heading:
            text = "#" * min(self.heading, 3) + " " + text
        elif self.lists:
            kind, n = self.lists[-1]
            indent = "  " * (len(self.lists) - 1)
            text = f"{indent}{n}. {text}" if kind == "ol" else f"{indent}- {text}"
            if self.out and self.out[-1][2] == "list":
                sep = "\n"                  # 목록 항목끼리는 줄바꿈 하나
            self.out.append((sep, text, "list"))
            return
        self.out.append((sep, text, "block"))

    def _write(self, text: str) -> None:
        if self.skip:
            return
        if self.cell is not None:
            self.cell.append(text)
        else:
            self.line.append(text)

    # ── 태그 ──
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in _SKIP:
            self.skip += 1
            return
        if self.skip:
            return
        if re.fullmatch(r"h[1-6]", tag):
            self._flush()
            self.heading = int(tag[1])
        elif tag in _BLOCK:
            if tag == "br" and self.cell is not None:
                self.cell.append(" ")
            elif tag == "br":
                self._flush()
                self.next_sep = "\n"       # <br>은 줄바꿈 하나
            else:
                self._flush()
        elif tag in ("ul", "ol"):
            self._flush()
            self.lists.append([tag, 0])
        elif tag == "li":
            self._flush()
            if self.lists:
                self.lists[-1][1] += 1
        elif tag == "table":
            self._flush()
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.table.append([])
        elif tag in ("td", "th") and self.table is not None:
            self.cell = []
        elif tag == "pre":
            self._flush()
            self.pre = True
            self._emit("```")
            self.next_sep = "\n"
        elif tag == "ac:structured-macro":
            name = a.get("ac:name", "")
            if name in _MACRO_TITLE:
                self._flush()
                self._emit(f"> [{_MACRO_TITLE[name]}]")
        elif tag == "ri:attachment":
            self._write(f"[이미지: {a.get('ri:filename', '첨부')}]")
        elif tag == "ri:page":
            self._write(a.get("ri:content-title", ""))
        elif tag == "img":
            self._write(f"[이미지: {a.get('alt') or a.get('src', '').rsplit('/', 1)[-1]}]")

    def handle_endtag(self, tag):
        if tag in _SKIP:
            self.skip = max(self.skip - 1, 0)
            return
        if self.skip:
            return
        if re.fullmatch(r"h[1-6]", tag):
            self._flush()
            self.heading = 0
        elif tag in _BLOCK or tag == "li":
            self._flush()
        elif tag in ("ul", "ol") and self.lists:
            self._flush()
            self.lists.pop()
        elif tag in ("td", "th") and self.cell is not None and self.table is not None:
            text = re.sub(r"\s+", " ", "".join(self.cell)).strip().replace("|", "\\|")
            if self.table:
                self.table[-1].append(text)
            self.cell = None
        elif tag == "table" and self.table is not None:
            rows = [r for r in self.table if r]
            if rows:
                width = max(len(r) for r in rows)
                rows = [r + [""] * (width - len(r)) for r in rows]
                lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
                lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
                self._emit("\n".join(lines))
            self.table = None
        elif tag == "pre":
            self._flush()
            self.pre = False
            self.out.append(("\n", "```", "block"))

    def handle_data(self, data):
        if self.skip:
            return
        self._write(data)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in ("br", "hr"):
            self.handle_endtag(tag)

    def _emit(self, text: str) -> None:
        self.out.append(("\n\n", text, "block"))

    def result(self) -> str:
        self._flush()
        joined = "".join((sep if i else "") + text for i, (sep, text, _) in enumerate(self.out))
        return re.sub(r"\n{3,}", "\n\n", joined).strip() + "\n"


def to_markdown(html: str) -> str:
    conv = _Converter()
    conv.feed(html)
    conv.close()
    return conv.result()


def html_title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
```

- [ ] **Step 6: 통과 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_fetch.py -q`
Expected: `5 passed`

- [ ] **Step 7: 커밋**

```bash
git add scripts/_tc_fetch.py scripts/_tc_html.py tests/unit/tc_library/conftest.py tests/unit/tc_library/test_tc_fetch.py
git commit -m "feat(tc-studio): C1 SSRF 방어 수집기와 HTML→markdown 변환"
```

---

## Task C2: 자격증명

**Files:**
- Create: `scripts/_tc_credentials.py`
- Modify: `.gitignore` (`config/jira_config.json` 줄 아래)
- Test: `tests/unit/tc_library/test_tc_credentials.py`

**Interfaces:**
- Produces: `confluence() -> {base_url, email, token, deployment: "cloud"|"dc", allow_private}`, `figma() -> {token}`, `confluence_headers(cfg)` (Cloud: `Basic base64(email:token)`, DC: `Bearer token`), `figma_headers()` (`X-Figma-Token`), `status() -> {confluence: {configured, base_url, email_masked, deployment}, figma: {configured}}`, `save(kind, fields) -> status()`. 미설정이면 `CREDENTIALS_MISSING`(409).

- [ ] **Step 1: gitignore** — `.gitignore`의 `config/jira_config.json` 아래:

```
# TC 스튜디오 연결 자격증명 (Phase 3)
config/confluence_config.json
config/figma_config.json
```

- [ ] **Step 2: 실패하는 테스트 작성** — `tests/unit/tc_library/test_tc_credentials.py`

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

import _tc_credentials as creds

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_credentials_are_saved_masked_and_env_wins(fake_web, monkeypatch):
    status = creds.save("confluence", {"base_url": "https://yafit.atlassian.net/", "email": "qa.lead@yafit.com",
                                       "token": "secret-token"})
    assert status["confluence"] == {"configured": True, "base_url": "https://yafit.atlassian.net",
                                    "email_masked": "qa****@yafit.com", "deployment": "cloud"}
    assert "secret-token" not in json.dumps(creds.status())
    creds.save("confluence", {"email": "qa.lead@yafit.com", "token": ""})       # 빈 토큰 = 기존 유지
    assert creds.confluence()["token"] == "secret-token"
    assert creds.confluence_headers(creds.confluence())["Authorization"].startswith("Basic ")
    creds.save("confluence", {"base_url": "https://wiki.corp.example", "deployment": "dc"})
    assert creds.confluence_headers(creds.confluence())["Authorization"] == "Bearer secret-token"
    monkeypatch.setenv("CONFLUENCE_TOKEN", "from-env")
    assert creds.confluence()["token"] == "from-env"
    with pytest.raises(Exception):
        creds.save("confluence", {"base_url": "ftp://x"})
    assert creds.status()["figma"] == {"configured": False}


def test_credential_files_are_gitignored():
    ignored = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "config/confluence_config.json" in ignored and "config/figma_config.json" in ignored
```

- [ ] **Step 3: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_credentials.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named '_tc_credentials'`

- [ ] **Step 4: 구현** — `scripts/_tc_credentials.py`

```python
"""Confluence·Figma 자격증명 (PRD §7, 로드맵 C2). jira_reporter.py와 같은 방식.

- 파일: config/confluence_config.json, config/figma_config.json (gitignore 대상)
- 환경변수가 있으면 파일보다 우선: CONFLUENCE_BASE_URL, CONFLUENCE_EMAIL, CONFLUENCE_TOKEN, FIGMA_TOKEN
- 화면·API에는 토큰을 절대 돌려주지 않는다 (status()는 마스킹 값만).
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from urllib.parse import urlparse

import _paths
from _tc_library import LibraryError


def _file(kind: str) -> Path:
    return _paths.PROJECT_ROOT / "config" / f"{kind}_config.json"


def _read(kind: str) -> dict:
    path = _file(kind)
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def confluence() -> dict:
    data = _read("confluence")
    base = (os.environ.get("CONFLUENCE_BASE_URL") or data.get("base_url") or "").rstrip("/")
    return {
        "base_url": base,
        "email": os.environ.get("CONFLUENCE_EMAIL") or data.get("email", ""),
        "token": os.environ.get("CONFLUENCE_TOKEN") or data.get("token", ""),
        # cloud: email + API 토큰 Basic, dc: 개인 액세스 토큰 Bearer
        "deployment": data.get("deployment")
        or ("cloud" if (urlparse(base).hostname or "").endswith(".atlassian.net") else "dc"),
        "allow_private": bool(data.get("allow_private", False)),
    }


def figma() -> dict:
    return {"token": os.environ.get("FIGMA_TOKEN") or _read("figma").get("token", "")}


def confluence_headers(cfg: dict) -> dict[str, str]:
    if not (cfg["base_url"] and cfg["token"]):
        raise LibraryError("Confluence 연결이 설정되지 않았습니다", "CREDENTIALS_MISSING", 409)
    if cfg["deployment"] == "cloud":
        raw = f"{cfg['email']}:{cfg['token']}".encode("utf-8")
        return {"Authorization": "Basic " + base64.b64encode(raw).decode("ascii"), "Accept": "application/json"}
    return {"Authorization": f"Bearer {cfg['token']}", "Accept": "application/json"}


def figma_headers() -> dict[str, str]:
    token = figma()["token"]
    if not token:
        raise LibraryError("Figma 연결이 설정되지 않았습니다", "CREDENTIALS_MISSING", 409)
    return {"X-Figma-Token": token}


def _mask_email(email: str) -> str:
    name, _, domain = email.partition("@")
    return f"{name[:2]}****@{domain}" if domain else ""


def status() -> dict:
    c, f = confluence(), figma()
    return {
        "confluence": {"configured": bool(c["base_url"] and c["token"]), "base_url": c["base_url"],
                       "email_masked": _mask_email(c["email"]), "deployment": c["deployment"]},
        "figma": {"configured": bool(f["token"])},
    }


def save(kind: str, fields: dict) -> dict:
    """PUT /api/tc-library/credentials/{kind}. 빈 토큰은 기존 값을 유지한다(다시 보여 주지 않으므로)."""
    if kind not in ("confluence", "figma"):
        raise LibraryError("알 수 없는 연결입니다", "INVALID_CREDENTIAL_KIND", 404)
    current = _read(kind)
    if kind == "confluence":
        base = str(fields.get("base_url", current.get("base_url", ""))).strip().rstrip("/")
        parsed = urlparse(base)
        if base and (parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.path not in ("", "/wiki")):
            raise LibraryError("base URL은 https://회사.atlassian.net 또는 https://confluence.회사.com 형식이어야 합니다", "INVALID_BASE_URL")
        current.update({"base_url": base, "email": str(fields.get("email", current.get("email", ""))).strip()})
        if fields.get("deployment") in ("cloud", "dc"):
            current["deployment"] = fields["deployment"]
        if "allow_private" in fields:
            current["allow_private"] = bool(fields["allow_private"])
    if str(fields.get("token", "")).strip():
        current["token"] = str(fields["token"]).strip()
    path = _file(kind)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return status()
```

- [ ] **Step 5: 통과 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_credentials.py -q`
Expected: `2 passed`

- [ ] **Step 6: 커밋**

```bash
git add .gitignore scripts/_tc_credentials.py tests/unit/tc_library/test_tc_credentials.py
git commit -m "feat(tc-studio): C2 Confluence·Figma 자격증명 (마스킹·환경변수 우선)"
```

---

## Task C3: 원격 소스 커넥터 (PRD URL · Confluence · Figma)

**Files:**
- Modify: `scripts/_tc_sources.py`, `scripts/_tc_generate.py` (아래 diff)
- Create: `scripts/_tc_connectors.py`
- Create: `tests/unit/tc_library/connector_fixtures.py` (녹화 응답)
- Test: `tests/unit/tc_library/test_tc_connectors.py`

**Interfaces:**
- Consumes: C1 `fetch Policy FetchError to_markdown html_title`, C2 헤더·설정, Phase 2 `add_fetched`의 바탕인 `_add`
- Produces:
  - `_tc_sources.add_fetched(bundle_id, *, kind, title, markdown, ref, version, origin, warnings=None, pages=0, assets=None)`, `asset_path(bundle_id, name)`, `find_source(versioned_ref) -> (bundle_id, entry) | None`; entry에 `origin`, `assets[]` 추가
  - `_tc_connectors.fetch_url(url)`, `add_url(bundle, url)`, `parse_confluence_url(url, cfg)`, `fetch_confluence_page(page_id, cfg)`, `add_confluence(bundle, url, *, children=False) -> [entry]`, `parse_figma_url(url)`, `figma_outline(frames)`, `fetch_figma(url, *, images=True)`, `add_figma(bundle, url)`, `ref_base(ref)`, `current_version(ref)`, `refetch_markdown(ref)`
  - Confluence API: Cloud `GET {base}/wiki/api/v2/pages/{id}?body-format=storage`, 하위 `…/pages/{id}/children?limit=20`, 버전 `…/pages/{id}` · DC `GET {base}/rest/api/content/{id}?expand=body.storage,version`, 하위 `…/content/{id}/child/page?limit=20` · 제목 주소 `…/rest/api/content?spaceKey=&title=&limit=1` · 짧은 링크 `{root}/x/{tiny}`의 리다이렉트 목적지에서 id
  - Figma API: `GET /v1/files/{key}/nodes?ids={node}&depth=6`, (node-id 없음) `GET /v1/files/{key}?depth=2`로 상위 프레임 최대 10개, `GET /v1/images/{key}?ids=…&format=png&scale=1`, 버전 `GET /v1/files/{key}?depth=1`
  - Figma outline 형식(프레임 = 섹션): `# 프레임명` / `- 화면 문구: "…"` / `- 컴포넌트: 이름 (State=…)` / `- 이동: 요소 선택 → 목적지`

- [ ] **Step 1: 녹화 응답** — `tests/unit/tc_library/connector_fixtures.py`

```python
"""Confluence·Figma 녹화 응답 (공식 REST 응답 형태를 줄인 것)."""
from __future__ import annotations

CLOUD = "https://yafit.atlassian.net"
PAGE_ID = "48213377"
STORAGE_V14 = ('<h1>8.6.0 배너 개편</h1><h2>배너 롤링 규칙</h2><p>배너는 3초마다 자동으로 다음 배너로 이동한다.</p>'
               '<h2>배너 선택 동작</h2><p>배너 선택 시 설정된 링크로 이동한다.</p>')
STORAGE_V15 = STORAGE_V14.replace("3초마다", "5초마다")


def cloud_page(version: int = 14, storage: str = STORAGE_V14, page_id: str = PAGE_ID, title: str = "8.6.0 혜택 탭 상단 배너 개편"):
    return {"id": page_id, "title": title, "version": {"number": version}, "body": {"storage": {"value": storage}}}


def setup_confluence(web, *, version: int = 14, storage: str = STORAGE_V14):
    import _tc_credentials as creds
    creds.save("confluence", {"base_url": CLOUD, "email": "qa@yafit.com", "token": "secret-token"})
    web.add(f"{CLOUD}/wiki/api/v2/pages/{PAGE_ID}?body-format=storage", json=cloud_page(version, storage))
    web.add(f"{CLOUD}/wiki/api/v2/pages/{PAGE_ID}", json={"id": PAGE_ID, "version": {"number": version}})


FIGMA_KEY = "Qx7aR2abc"
FIGMA_NODE = {
    "name": "야핏무브 8.6.0", "version": "4410", "lastModified": "2026-09-20T00:00:00Z",
    "nodes": {"12:345": {"document": {
        "id": "12:345", "name": "혜택_상단배너", "type": "FRAME", "children": [
            {"id": "12:346", "name": "title", "type": "TEXT", "characters": "혜택"},
            {"id": "12:347", "name": "fallback", "type": "TEXT", "characters": "혜택을 준비하고 있어요"},
            {"id": "12:348", "name": "Banner", "type": "INSTANCE", "transitionNodeID": "20:1",
             "componentProperties": {"State#1": {"type": "VARIANT", "value": "Default"}}},
        ]}}},
}


def setup_figma(web, *, version: str = "4410"):
    import _tc_credentials as creds
    creds.save("figma", {"token": "figd_secret"})
    node = dict(FIGMA_NODE, version=version)
    web.add(f"https://api.figma.com/v1/files/{FIGMA_KEY}/nodes?ids=12%3A345&depth=6", json=node)
    web.add(f"https://api.figma.com/v1/images/{FIGMA_KEY}?ids=12%3A345&format=png&scale=1",
            json={"images": {"12:345": "https://figma-alpha-api.s3.us-west-2.amazonaws.com/images/abc"}})
    web.add("https://figma-alpha-api.s3.us-west-2.amazonaws.com/images/abc", b"\x89PNG\r\n\x1a\nfake")
    web.add(f"https://api.figma.com/v1/files/{FIGMA_KEY}?depth=1", json={"name": node["name"], "version": version})


FIGMA_URL = f"https://www.figma.com/design/{FIGMA_KEY}/Yafit?node-id=12-345&t=abc"
```

- [ ] **Step 2: 실패하는 테스트 작성** — `tests/unit/tc_library/test_tc_connectors.py`

```python
from __future__ import annotations

import pytest

import _tc_connectors as conn
import _tc_credentials as creds
import _tc_generate as gen
import _tc_library as lib
import _tc_sources as src
from _tc_fetch import FetchError
from _tc_template import analyze_workbook
from _tc_xlsx_import import import_workbook
from tests.unit.tc_library.connector_fixtures import (
    CLOUD, FIGMA_KEY, FIGMA_URL, PAGE_ID, cloud_page, setup_confluence, setup_figma,
)
from tests.unit.tc_library.source_fixtures import make_pdf

SUITE = "야핏무브"


def test_public_url_html_pdf_and_text(library_dir, fake_web):
    fake_web.add("https://docs.example.com/prd", "<title>PRD</title><h1>배너</h1><p>3초마다 이동</p>",
                 headers={"Content-Type": "text/html; charset=utf-8"})
    fake_web.add("https://docs.example.com/spec.pdf", make_pdf(["Rotate every 3s"]),
                 headers={"Content-Type": "application/pdf"})
    fake_web.add("https://docs.example.com/a.bin", b"\x00", headers={"Content-Type": "application/octet-stream"})
    bundle = src.new_bundle()
    html = conn.add_url(bundle, "https://docs.example.com/prd")
    pdf = conn.add_url(bundle, "https://docs.example.com/spec.pdf")

    assert (html["kind"], html["title"], html["origin"]) == ("url", "PRD", "https://docs.example.com/prd")
    assert html["ref"].startswith("url:") and "# 배너" in src.read_text(bundle, html["source_id"])
    assert pdf["pages"] == 1
    with pytest.raises(FetchError) as exc:
        conn.add_url(bundle, "https://docs.example.com/a.bin")
    assert exc.value.code == "UNSUPPORTED_REMOTE_TYPE"
    with pytest.raises(FetchError):
        conn.add_url(bundle, "http://docs.example.com/prd")


def test_confluence_url_shapes():
    cfg = {"base_url": CLOUD}
    assert conn.parse_confluence_url(f"{CLOUD}/wiki/spaces/MOVE/pages/{PAGE_ID}/Title", cfg) == {"page_id": PAGE_ID}
    assert conn.parse_confluence_url(f"{CLOUD}/wiki/pages/viewpage.action?pageId=42", cfg) == {"page_id": "42"}
    assert conn.parse_confluence_url(f"{CLOUD}/wiki/x/AbC_1", cfg) == {"tiny": "AbC_1"}
    assert conn.parse_confluence_url(f"{CLOUD}/display/MOVE/8.6.0+Banner", cfg) == {"space": "MOVE", "title": "8.6.0 Banner"}
    for bad in ("https://evil.example.com/wiki/pages/1", f"{CLOUD}/wiki/spaces/MOVE/overview"):
        with pytest.raises(FetchError):
            conn.parse_confluence_url(bad, cfg)


def test_confluence_cloud_page_children_and_tiny_link(library_dir, fake_web):
    setup_confluence(fake_web)
    fake_web.add(f"{CLOUD}/wiki/api/v2/pages/{PAGE_ID}/children?limit=20", json={"results": [{"id": "7"}]})
    fake_web.add(f"{CLOUD}/wiki/api/v2/pages/7?body-format=storage",
                 json=cloud_page(3, "<p>하위 페이지 본문</p>", page_id="7", title="하위"))
    fake_web.add(f"{CLOUD}/wiki/x/AbC", status=302, headers={"Location": f"{CLOUD}/wiki/spaces/MOVE/pages/{PAGE_ID}/T"})
    fake_web.add(f"{CLOUD}/wiki/spaces/MOVE/pages/{PAGE_ID}/T", "<html></html>")
    bundle = src.new_bundle()

    entries = conn.add_confluence(bundle, f"{CLOUD}/wiki/spaces/MOVE/pages/{PAGE_ID}/x", children=True)
    assert [e["ref"] for e in entries] == [f"conf:{PAGE_ID}@v14", "conf:7@v3"]
    assert entries[0]["origin"] == f"{CLOUD}/wiki/pages/viewpage.action?pageId={PAGE_ID}"
    assert "## 배너 롤링 규칙" in src.read_text(bundle, entries[0]["source_id"])
    sent = dict(fake_web.calls)[f"{CLOUD}/wiki/api/v2/pages/{PAGE_ID}?body-format=storage"]
    assert sent["Authorization"].startswith("Basic ")

    other = src.new_bundle()
    assert conn.add_confluence(other, f"{CLOUD}/wiki/x/AbC")[0]["ref"] == f"conf:{PAGE_ID}@v14"


def test_confluence_dc_uses_rest_api_and_bearer(library_dir, fake_web):
    fake_web.private.add("wiki.corp.example")
    creds.save("confluence", {"base_url": "https://wiki.corp.example", "deployment": "dc", "token": "pat",
                              "allow_private": True})
    fake_web.add("https://wiki.corp.example/rest/api/content/9?expand=body.storage,version",
                 json=cloud_page(2, "<p>DC 본문</p>", page_id="9", title="DC"))
    entry = conn.add_confluence(src.new_bundle(), "https://wiki.corp.example/pages/viewpage.action?pageId=9")[0]
    assert entry["ref"] == "conf:9@v2"
    assert dict(fake_web.calls)["https://wiki.corp.example/rest/api/content/9?expand=body.storage,version"]["Authorization"] == "Bearer pat"


def test_figma_frame_outline_and_images(library_dir, fake_web):
    setup_figma(fake_web)
    bundle = src.new_bundle()
    entry = conn.add_figma(bundle, FIGMA_URL)

    assert entry["ref"] == f"figma:{FIGMA_KEY}/12:345@4410"
    assert entry["title"] == "야핏무브 8.6.0 / 혜택_상단배너"
    text = src.read_text(bundle, entry["source_id"])
    assert '- 화면 문구: "혜택을 준비하고 있어요"' in text
    assert "- 컴포넌트: Banner (State=Default)" in text and "- 이동: Banner 선택 → 20:1" in text
    assert entry["assets"] == ["01_혜택_상단배너.png"]
    assert src.asset_path(bundle, entry["assets"][0]).read_bytes().startswith(b"\x89PNG")
    assert dict(fake_web.calls)[f"https://api.figma.com/v1/images/{FIGMA_KEY}?ids=12%3A345&format=png&scale=1"]["X-Figma-Token"] == "figd_secret"
    with pytest.raises(FetchError):
        conn.parse_figma_url("https://www.figma.com/community/file/1")


def test_missing_credentials_are_reported(library_dir, fake_web):
    with pytest.raises(Exception) as exc:
        conn.add_figma(src.new_bundle(), FIGMA_URL)
    assert exc.value.code == "CREDENTIALS_MISSING"


def test_figma_text_becomes_verified_ui_text(library_dir, template_xlsx, fake_web, fake_claude):
    profiles = analyze_workbook(template_xlsx)
    lib.save_template(SUITE, template_xlsx, profiles)
    lib.import_cases(SUITE, ["혜택"], import_workbook(template_xlsx, profiles, ["혜택"], {"혜택": "BEN"}), "t")
    setup_figma(fake_web)
    bundle = src.new_bundle()
    conn.add_figma(bundle, FIGMA_URL)
    job = gen.create_job(SUITE, bundle_id=bundle, target={"sheet": "혜택", "path": ["혜택 탭", "상단 배너"]}, profile="기본")
    gen.run_job(job["job_id"])
    draft = lib.filter_cases(lib.load_cases(SUITE), {"job": job["job_id"]})[0]
    assert draft["source_refs"][0].startswith(f"figma:{FIGMA_KEY}/12:345@4410#§")
    assert all(b["verified"] for b in draft["bullets"])
```

- [ ] **Step 3: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_connectors.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named '_tc_connectors'`

- [ ] **Step 4: 소스 번들·생성기 수정**

```diff
--- a/scripts/_tc_sources.py
+++ b/scripts/_tc_sources.py
@@ -167,7 +167,8 @@
 
 
 def _add(bundle_id: str, kind: str, title: str, markdown: str, digest: str,
-         pages: int, warnings: list[str]) -> dict:
+         pages: int, warnings: list[str], *, ref: str = "", version: str = "",
+         origin: str = "", assets: dict[str, bytes] | None = None) -> dict:
     d = _bundle_dir(bundle_id)
     if not (d / "manifest.json").exists():
         raise SourceError("소스 묶음이 없습니다", "BUNDLE_NOT_FOUND", 404)
@@ -178,19 +179,26 @@
     entry: dict = {}
 
     def mutate(manifest: dict) -> dict:
-        ref = f"{kind}:{digest[:12]}"
-        if any(s["ref"] == ref for s in manifest["sources"]):
+        source_ref = ref or f"{kind}:{digest[:12]}"
+        if any(s["ref"] == source_ref for s in manifest["sources"]):
             raise SourceError("이미 추가한 소스입니다", "SOURCE_EXISTS", 409)
         # 지운 번호를 다시 쓰지 않는다 (지운 뒤 추가해도 s01·s02가 겹치지 않게)
         n = max([int(x["source_id"][1:]) for x in manifest["sources"]] + [manifest.get("last_n", 0)]) + 1
         manifest["last_n"] = n
         filename = f"{n:02d}_{_slug(title)}.md"
         (d / filename).write_text(markdown, encoding="utf-8")
+        asset_names = []
+        for name, data in (assets or {}).items():
+            safe = f"{n:02d}_{_slug(name)}.png"
+            (d / "assets").mkdir(exist_ok=True)
+            (d / "assets" / safe).write_bytes(data)
+            asset_names.append(safe)
         entry.update({
-            "source_id": f"s{n:02d}", "kind": kind, "title": title, "ref": ref,
-            "version": digest[:12], "sha256": digest, "chars": len(markdown), "pages": pages,
+            "source_id": f"s{n:02d}", "kind": kind, "title": title, "ref": source_ref,
+            "version": version or digest[:12], "sha256": digest, "chars": len(markdown), "pages": pages,
             "sections": len(split_sections(markdown)), "truncated": truncated,
-            "warnings": warnings, "file": filename, "added_at": now_iso(),
+            "warnings": warnings, "file": filename, "origin": origin, "assets": asset_names,
+            "added_at": now_iso(),
         })
         manifest["sources"].append(dict(entry))
         return manifest
@@ -219,6 +227,41 @@
     return _add(bundle_id, "paste", title, text, hashlib.sha256(raw).hexdigest(), 0, [])
 
 
+def add_fetched(bundle_id: str, *, kind: str, title: str, markdown: str, ref: str, version: str,
+                origin: str, warnings: list[str] | None = None, pages: int = 0,
+                assets: dict[str, bytes] | None = None) -> dict:
+    """원격 소스(url·conf·figma) 추가 (Phase 3). ref에는 버전이 들어간다: "conf:48213377@v14"."""
+    if not markdown.strip():
+        raise SourceError("가져온 문서에 본문이 없습니다", "EMPTY_SOURCE")
+    digest = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
+    return _add(bundle_id, kind, title, markdown, digest, pages, list(warnings or []),
+                ref=ref, version=version, origin=origin, assets=assets)
+
+
+def asset_path(bundle_id: str, name: str) -> Path:
+    if not re.fullmatch(r"\d\d_[\w가-힣]+\.png", name):
+        raise SourceError("파일 이름이 올바르지 않습니다", "INVALID_ASSET")
+    path = _bundle_dir(bundle_id) / "assets" / name
+    if not path.exists():
+        raise SourceError("이미지가 없습니다", "ASSET_NOT_FOUND", 404)
+    return path
+
+
+def find_source(ref: str) -> tuple[str, dict] | None:
+    """버전 포함 ref("conf:123@v14")를 가진 소스를 모든 묶음에서 찾는다 (가장 최근 묶음 우선)."""
+    root = sources_root()
+    if not root.exists():
+        return None
+    for d in sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
+        manifest = d / "manifest.json"
+        if not manifest.exists():
+            continue
+        for entry in json.loads(manifest.read_text(encoding="utf-8"))["sources"]:
+            if entry["ref"] == ref:
+                return d.name, entry
+    return None
+
+
 def remove_source(bundle_id: str, source_id: str) -> None:
     d = _bundle_dir(bundle_id)
 
```

```diff
--- a/scripts/_tc_generate.py
+++ b/scripts/_tc_generate.py
@@ -264,7 +264,8 @@
             allowed = {i["ref"]: i["text"] for i in chunk}
             drafts = []
             for raw in output.get("cases", []):
-                draft, errors = build_draft(raw, target=target, allowed=allowed, job_id=job_id)
+                draft, errors = build_draft(raw, target=target, allowed=allowed, job_id=job_id,
+                                            verified_kinds=("figma",))   # Figma 화면 문구 = 확인된 문구
                 if errors:
                     invalid.append({"section": n + 1, "raw": raw, "errors": errors})
                     sections[n]["invalid"] += 1
```

- [ ] **Step 5: 커넥터** — `scripts/_tc_connectors.py`

```python
"""원격 소스 수집 — PRD URL · Confluence · Figma (PRD F1.3, F1.4, 로드맵 C3~C5).

모든 요청은 _tc_fetch.fetch()를 거친다 (호스트 허용 목록·내부망 차단·리다이렉트 재검사·크기 상한).
사용자가 준 URL은 **id를 뽑는 데만** 쓰고, API 요청 주소는 서버가 설정값으로 조립한다.

ref 형식 (버전 포함):
  url:{본문 sha256 12자}            (version = 같은 값)
  conf:{page_id}@v{version.number}
  figma:{file_key}/{node_id|file}@{figma version}
"""
from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse

import _tc_credentials as creds
from _tc_fetch import FetchError, Policy, fetch
from _tc_html import html_title, to_markdown
from _tc_sources import add_fetched, extract

FIGMA_API = "https://api.figma.com"
FIGMA_IMAGE_HOSTS = ("figma-alpha-api.s3.us-west-2.amazonaws.com", "*.figma.com")
MAX_FIGMA_TEXTS = 2000
MAX_FIGMA_FRAMES = 10
MAX_CHILD_PAGES = 20


# ── PRD URL (공개 HTTPS 문서) ─────────────────────────────────
def fetch_url(url: str) -> dict:
    """공개 문서 1건 → {title, markdown, version, origin, pages, warnings}. 모든 공개 호스트 허용(내부망은 차단)."""
    if urlparse(url).scheme != "https":
        raise FetchError("https 주소만 가져올 수 있습니다", "URL_NOT_ALLOWED")
    resp = fetch(url, Policy(hosts=("*",)))
    ctype = resp.headers.get("content-type", "").split(";")[0].strip().lower()
    name = unquote(urlparse(resp.url).path.rsplit("/", 1)[-1]) or "document"
    if ctype == "application/pdf" or name.lower().endswith(".pdf"):
        markdown, pages, warnings = extract("remote.pdf", resp.body)
        title = name
    elif "wordprocessingml" in ctype or name.lower().endswith(".docx"):
        markdown, pages, warnings = extract("remote.docx", resp.body)
        title = name
    elif ctype in ("text/html", "application/xhtml+xml") or not ctype:
        html = resp.text()
        markdown, pages, warnings = to_markdown(html), 0, []
        title = html_title(html) or urlparse(url).hostname
    elif ctype.startswith("text/"):
        markdown, pages, warnings = resp.text(), 0, []
        title = name
    else:
        raise FetchError(f"지원하지 않는 문서 형식입니다: {ctype}", "UNSUPPORTED_REMOTE_TYPE")
    version = hashlib.sha256(markdown.encode("utf-8")).hexdigest()[:12]
    return {"title": title, "markdown": markdown, "version": version, "origin": url,
            "pages": pages, "warnings": warnings}


def add_url(bundle_id: str, url: str) -> dict:
    doc = fetch_url(url)
    return add_fetched(bundle_id, kind="url", title=doc["title"], markdown=doc["markdown"],
                       ref=f"url:{doc['version']}", version=doc["version"], origin=url,
                       pages=doc["pages"], warnings=doc["warnings"])


# ── Confluence ───────────────────────────────────────────────
def _conf_policy(cfg: dict) -> Policy:
    host = urlparse(cfg["base_url"]).hostname or ""
    return Policy(hosts=(host,), private_hosts=(host,) if cfg["allow_private"] else (),
                  http_hosts=(host,) if cfg["base_url"].startswith("http://") else (),
                  headers=creds.confluence_headers(cfg))


def _api_root(cfg: dict) -> str:
    base = cfg["base_url"]
    if cfg["deployment"] == "cloud":
        return base if base.endswith("/wiki") else base + "/wiki"
    return base


def parse_confluence_url(url: str, cfg: dict) -> dict:
    """→ {"page_id"} 또는 {"space", "title"} 또는 {"tiny"}. 설정한 base와 다른 호스트면 거부."""
    parsed = urlparse(url)
    base_host = urlparse(cfg["base_url"]).hostname
    if not base_host:
        raise FetchError("Confluence 연결이 설정되지 않았습니다", "CREDENTIALS_MISSING", 409)
    if (parsed.hostname or "").lower() != base_host.lower():
        raise FetchError(f"설정한 Confluence 주소({base_host})의 페이지가 아닙니다", "HOST_NOT_ALLOWED")
    if m := re.search(r"/pages/(\d+)", parsed.path):
        return {"page_id": m.group(1)}
    if page_id := parse_qs(parsed.query).get("pageId", [""])[0]:
        if page_id.isdigit():
            return {"page_id": page_id}
    if m := re.search(r"/x/([A-Za-z0-9_-]+)", parsed.path):
        return {"tiny": m.group(1)}
    if m := re.search(r"/display/([^/]+)/([^/?#]+)", parsed.path):
        return {"space": unquote(m.group(1)), "title": unquote(m.group(2)).replace("+", " ")}
    raise FetchError("페이지 ID를 찾을 수 없습니다. /pages/{id} 또는 pageId= 가 들어간 주소를 넣어 주세요",
                     "PAGE_ID_NOT_FOUND")


def _resolve_page_id(target: dict, cfg: dict) -> str:
    if "page_id" in target:
        return target["page_id"]
    root, policy = _api_root(cfg), _conf_policy(cfg)
    if "tiny" in target:                       # /x/{tiny}는 같은 호스트의 /pages/{id}로 리다이렉트된다
        resp = fetch(f"{root}/x/{quote(target['tiny'])}", policy)
        if m := re.search(r"/pages/(\d+)", resp.url) or re.search(r"pageId=(\d+)", resp.url):
            return m.group(1)
        raise FetchError("짧은 링크에서 페이지를 찾지 못했습니다", "PAGE_ID_NOT_FOUND")
    path = "/rest/api/content"
    query = urlencode({"spaceKey": target["space"], "title": target["title"], "limit": 1})
    results = fetch(f"{root}{path}?{query}", policy).json().get("results", [])
    if not results:
        raise FetchError("제목으로 페이지를 찾지 못했습니다", "NOT_FOUND_REMOTE", 404)
    return str(results[0]["id"])


def fetch_confluence_page(page_id: str, cfg: dict) -> dict:
    """→ {page_id, title, version, markdown}."""
    root, policy = _api_root(cfg), _conf_policy(cfg)
    if cfg["deployment"] == "cloud":
        data = fetch(f"{root}/api/v2/pages/{page_id}?body-format=storage", policy).json()
        html = data["body"]["storage"]["value"]
    else:
        data = fetch(f"{root}/rest/api/content/{page_id}?expand=body.storage,version", policy).json()
        html = data["body"]["storage"]["value"]
    return {"page_id": str(data["id"]), "title": data["title"], "version": int(data["version"]["number"]),
            "markdown": to_markdown(html)}


def confluence_version(page_id: str, cfg: dict) -> int:
    root, policy = _api_root(cfg), _conf_policy(cfg)
    url = (f"{root}/api/v2/pages/{page_id}" if cfg["deployment"] == "cloud"
           else f"{root}/rest/api/content/{page_id}?expand=version")
    return int(fetch(url, policy).json()["version"]["number"])


def _child_ids(page_id: str, cfg: dict) -> list[str]:
    root, policy = _api_root(cfg), _conf_policy(cfg)
    url = (f"{root}/api/v2/pages/{page_id}/children?limit={MAX_CHILD_PAGES}" if cfg["deployment"] == "cloud"
           else f"{root}/rest/api/content/{page_id}/child/page?limit={MAX_CHILD_PAGES}")
    return [str(r["id"]) for r in fetch(url, policy).json().get("results", [])][:MAX_CHILD_PAGES]


def add_confluence(bundle_id: str, url: str, *, children: bool = False) -> list[dict]:
    cfg = creds.confluence()
    page_id = _resolve_page_id(parse_confluence_url(url, cfg), cfg)
    ids = [page_id] + (_child_ids(page_id, cfg) if children else [])
    entries = []
    for pid in ids:
        page = fetch_confluence_page(pid, cfg)
        origin = f"{_api_root(cfg)}/pages/viewpage.action?pageId={pid}"
        entries.append(add_fetched(bundle_id, kind="conf", title=page["title"], markdown=page["markdown"],
                                   ref=f"conf:{pid}@v{page['version']}", version=f"v{page['version']}",
                                   origin=origin))
    return entries


# ── Figma ────────────────────────────────────────────────────
def parse_figma_url(url: str) -> dict:
    parsed = urlparse(url)
    if not (parsed.hostname or "").endswith("figma.com"):
        raise FetchError("Figma 파일 주소가 아닙니다", "HOST_NOT_ALLOWED")
    m = re.match(r"/(?:file|design|proto)/([A-Za-z0-9]+)", parsed.path)
    if not m:
        raise FetchError("Figma 파일 주소가 아닙니다. /file/ 또는 /design/ 주소를 넣어 주세요", "FIGMA_KEY_NOT_FOUND")
    node = parse_qs(parsed.query).get("node-id", [""])[0].replace("-", ":")
    return {"file_key": m.group(1), "node_id": node if re.fullmatch(r"\d+:\d+", node) else ""}


def _figma_policy(hosts=("api.figma.com",)) -> Policy:
    return Policy(hosts=hosts, headers=creds.figma_headers())


def _walk(node: dict, frame: str, out: dict, names: dict) -> None:
    names[node.get("id", "")] = node.get("name", "")
    kind = node.get("type")
    if kind == "TEXT" and node.get("characters", "").strip() and len(out["texts"]) < MAX_FIGMA_TEXTS:
        out["texts"].append((frame, node["characters"].strip()))
    elif kind == "INSTANCE":
        props = node.get("componentProperties") or {}
        variants = ", ".join(f"{k.split('#')[0]}={v.get('value')}" for k, v in props.items()
                             if v.get("type") == "VARIANT")
        out["components"].append((frame, node.get("name", ""), variants))
    targets = [node.get("transitionNodeID")] + [
        (i.get("actions") or [{}])[0].get("destinationId") for i in node.get("interactions") or []]
    for target in filter(None, targets):
        out["flows"].append((frame, node.get("name", ""), target))
    for child in node.get("children") or []:
        _walk(child, frame, out, names)


def figma_outline(frames: list[dict]) -> str:
    """프레임 목록 → markdown (프레임 = 섹션). 화면 문구·컴포넌트 상태·프로토타입 이동을 적는다."""
    names: dict[str, str] = {}
    blocks = []
    for frame in frames:
        out = {"texts": [], "components": [], "flows": []}
        _walk(frame, frame.get("name", ""), out, names)
        blocks.append((frame, out))
    lines = []
    for frame, out in blocks:
        lines.append(f"# {frame.get('name', '프레임')}")
        lines += [f'- 화면 문구: "{t}"' for _, t in out["texts"]]
        lines += [f"- 컴포넌트: {n}{f' ({v})' if v else ''}" for _, n, v in out["components"]]
        lines += [f"- 이동: {src or '프레임'} 선택 → {names.get(dst, dst)}" for _, src, dst in out["flows"]]
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def fetch_figma(url: str, *, images: bool = True) -> dict:
    """→ {file_key, node_id, name, version, markdown, frames[{id,name}], images{name: png bytes}}."""
    target = parse_figma_url(url)
    key, node = target["file_key"], target["node_id"]
    policy = _figma_policy()
    if node:
        data = fetch(f"{FIGMA_API}/v1/files/{key}/nodes?ids={quote(node)}&depth=6", policy).json()
        root = data["nodes"][node]["document"]
        frames = [root] if root.get("type") in ("FRAME", "COMPONENT", "SECTION") else \
            [c for c in root.get("children", []) if c.get("type") in ("FRAME", "COMPONENT")][:MAX_FIGMA_FRAMES]
    else:
        meta = fetch(f"{FIGMA_API}/v1/files/{key}?depth=2", policy).json()
        ids = [c["id"] for page in meta["document"].get("children", [])
               for c in page.get("children", []) if c.get("type") == "FRAME"][:MAX_FIGMA_FRAMES]
        if not ids:
            raise FetchError("가져올 프레임이 없습니다", "EMPTY_SOURCE")
        data = fetch(f"{FIGMA_API}/v1/files/{key}/nodes?ids={quote(','.join(ids))}&depth=6", policy).json()
        data.setdefault("version", meta.get("version"))
        data.setdefault("name", meta.get("name"))
        frames = [data["nodes"][i]["document"] for i in ids if i in data["nodes"]]
    pngs: dict[str, bytes] = {}
    if images and frames:
        ids = ",".join(f["id"] for f in frames[:MAX_FIGMA_FRAMES])
        urls = fetch(f"{FIGMA_API}/v1/images/{key}?ids={quote(ids)}&format=png&scale=1", policy).json().get("images", {})
        image_policy = Policy(hosts=FIGMA_IMAGE_HOSTS, max_bytes=10 * 1024 * 1024)
        for frame in frames[:MAX_FIGMA_FRAMES]:
            if urls.get(frame["id"]):
                pngs[frame.get("name", frame["id"])] = fetch(urls[frame["id"]], image_policy).body
    return {"file_key": key, "node_id": node, "name": data.get("name", key), "version": str(data.get("version", "")),
            "markdown": figma_outline(frames), "frames": [{"id": f["id"], "name": f.get("name", "")} for f in frames],
            "images": pngs}


def figma_version(file_key: str) -> str:
    return str(fetch(f"{FIGMA_API}/v1/files/{file_key}?depth=1", _figma_policy()).json().get("version", ""))


def add_figma(bundle_id: str, url: str) -> dict:
    doc = fetch_figma(url)
    node = doc["node_id"] or "file"
    title = doc["name"] + (f" / {doc['frames'][0]['name']}" if doc["node_id"] and doc["frames"] else "")
    warnings = [] if doc["images"] else ["프레임 이미지를 받지 못했습니다"]
    return add_fetched(bundle_id, kind="figma", title=title, markdown=doc["markdown"],
                       ref=f"figma:{doc['file_key']}/{node}@{doc['version']}", version=doc["version"],
                       origin=url, warnings=warnings, assets=doc["images"])


def ref_base(ref: str) -> str:
    """"conf:123@v14#§2" → "conf:123", "figma:KEY/1:2@99#§1" → "figma:KEY/1:2"."""
    return ref.split("#", 1)[0].split("@", 1)[0]


def current_version(ref: str) -> str:
    """버전 포함 ref의 현재 원격 버전 (conf → "v15", figma → 버전 id, url → 본문 해시)."""
    base = ref_base(ref)
    kind, _, rest = base.partition(":")
    if kind == "conf":
        return f"v{confluence_version(rest, creds.confluence())}"
    if kind == "figma":
        return figma_version(rest.split("/", 1)[0])
    raise FetchError(f"버전을 확인할 수 없는 출처입니다: {kind}", "UNSUPPORTED_REF")


def refetch_markdown(ref: str) -> str:
    """현재 버전 본문 (차이 비교용)."""
    base = ref_base(ref)
    kind, _, rest = base.partition(":")
    if kind == "conf":
        return fetch_confluence_page(rest, creds.confluence())["markdown"]
    if kind == "figma":
        key, _, node = rest.partition("/")
        url = f"https://www.figma.com/design/{key}/x" + (f"?node-id={node.replace(':', '-')}" if node != "file" else "")
        return fetch_figma(url, images=False)["markdown"]
    raise FetchError(f"다시 가져올 수 없는 출처입니다: {kind}", "UNSUPPORTED_REF")
```

- [ ] **Step 6: 통과 확인 + 회귀**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_connectors.py tests/unit/tc_library/test_tc_sources.py tests/unit/tc_library/test_tc_generate.py -q`
Expected: `20 passed`

- [ ] **Step 7: 커밋**

```bash
git add scripts/_tc_sources.py scripts/_tc_generate.py scripts/_tc_connectors.py tests/unit/tc_library/connector_fixtures.py tests/unit/tc_library/test_tc_connectors.py
git commit -m "feat(tc-studio): C3 PRD URL·Confluence·Figma 소스 커넥터"
```

---

## Task C4: 출처 버전 추적

**Files:**
- Modify: `scripts/_tc_model.py`, `scripts/_tc_library.py` (아래 diff)
- Create: `scripts/_tc_source_watch.py`
- Test: `tests/unit/tc_library/test_tc_source_watch.py`

**Interfaces:**
- Produces:
  - 케이스 필드 `flags: {source_change: {ref, from, to, to_ref, at}}`, `filter_cases(…, {"needs_review": "1"})`, 트리 `needs_review` 집계에 표시 포함
  - `set_flag(suite, case_id, name, value|None)`, `replace_source_version(suite, case_id, old_ref, new_ref)` — rev 불변
  - `RESERVED_SUITES`에 `credentials`, `source-diff` 추가
  - `scan(suite) -> {checked, changes[{ref, from, to, case_ids}], errors[{ref, error, code}]}` (conf·figma만), `flagged(suite)`, `ack(suite, case_id) -> case`, `diff(ref) -> {old_available, lines[{op: " "|"-"|"+"|"@", text}]}`

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/unit/tc_library/test_tc_source_watch.py`

```python
from __future__ import annotations

import _tc_connectors as conn
import _tc_library as lib
import _tc_source_watch as watch
import _tc_sources as src
from _tc_template import analyze_workbook
from _tc_xlsx_import import import_workbook
from tests.unit.tc_library.connector_fixtures import CLOUD, PAGE_ID, STORAGE_V15, setup_confluence

SUITE = "야핏무브"


def test_source_change_scan_flag_diff_and_ack(library_dir, template_xlsx, fake_web):
    profiles = analyze_workbook(template_xlsx)
    lib.save_template(SUITE, template_xlsx, profiles)
    lib.import_cases(SUITE, ["혜택"], import_workbook(template_xlsx, profiles, ["혜택"], {"혜택": "BEN"}), "t")
    setup_confluence(fake_web)
    conn.add_confluence(src.new_bundle(), f"{CLOUD}/wiki/spaces/MOVE/pages/{PAGE_ID}")
    lib.add_source_refs(SUITE, "BEN_0002", [f"conf:{PAGE_ID}@v14#§2"])

    assert watch.scan(SUITE)["changes"] == []
    setup_confluence(fake_web, version=15, storage=STORAGE_V15)
    result = watch.scan(SUITE)
    assert result["changes"] == [{"ref": f"conf:{PAGE_ID}@v14", "from": "v14", "to": "v15", "case_ids": ["BEN_0002"]}]
    assert [c["case_id"] for c in lib.filter_cases(lib.load_cases(SUITE), {"needs_review": "1"})] == ["BEN_0002"]
    assert watch.flagged(SUITE)[0]["case_ids"] == ["BEN_0002"]

    lines = watch.diff(f"conf:{PAGE_ID}@v14#§2")["lines"]
    assert {"op": "-", "text": "배너는 3초마다 자동으로 다음 배너로 이동한다."} in lines
    assert {"op": "+", "text": "배너는 5초마다 자동으로 다음 배너로 이동한다."} in lines

    case = watch.ack(SUITE, "BEN_0002")
    assert f"conf:{PAGE_ID}@v15#§2" in case["source_refs"] and "source_change" not in case["flags"]
    assert case["rev"] == 1
    assert lib.build_tree(lib.load_cases(SUITE))[0]["needs_review"] == 0
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_source_watch.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named '_tc_source_watch'`

- [ ] **Step 3: 모델·저장소 수정**

```diff
--- a/scripts/_tc_model.py
+++ b/scripts/_tc_model.py
@@ -34,6 +34,8 @@
         "updated_at": now_iso(),
         # 생성 초안 정보 (Phase 2): job_id, source_quote, duplicates[{case_id, similarity}]
         "draft_meta": {},
+        # 검토 표시 (Phase 3): source_change {ref, from, to, at} — 상태(status)와 따로 둔다 (명세 피드백 #7)
+        "flags": {},
     }
     case.update(fields)
     case["path"] = (list(case["path"]) + ["", "", ""])[:3]
```

```diff
--- a/scripts/_tc_library.py
+++ b/scripts/_tc_library.py
@@ -34,7 +34,7 @@
 
 
 # API 경로 조각과 겹치는 이름은 스위트로 쓸 수 없다 (/api/tc-library/{profiles|sources|jobs|…})
-RESERVED_SUITES = {"import", "exports", "sources", "profiles", "jobs"}
+RESERVED_SUITES = {"import", "exports", "sources", "profiles", "jobs", "credentials", "source-diff"}
 
 
 def suite_dir(suite: str) -> Path:
@@ -323,6 +323,8 @@
             continue
         if query.get("job") and case.get("draft_meta", {}).get("job_id") != query["job"]:
             continue
+        if query.get("needs_review") == "1" and not case.get("flags", {}).get("source_change"):
+            continue
         if q:
             haystack = json.dumps([case["feature"], case["precondition"], case["steps"],
                                    case["expected"], case["bullets"]], ensure_ascii=False)
@@ -350,7 +352,7 @@
                 children.append(node)
             node["count"] += 1
             node["draft"] += case["status"] == "draft"
-            node["needs_review"] += case["status"] == "needs_review"
+            node["needs_review"] += case["status"] == "needs_review" or bool(case.get("flags", {}).get("source_change"))
             node["invalid"] += case["has_error"]
             children = node["children"]
     return roots
@@ -417,8 +419,42 @@
     def mutate(data: dict) -> dict:
         case = _find(data, case_id)
         case["source_refs"] = list(dict.fromkeys(case["source_refs"] + refs))
+        out["case"] = dict(case)
+        return data
+
+    update_state(_cases_path(suite), mutate)
+    return out["case"]
+
+
+def set_flag(suite: str, case_id: str, name: str, value) -> dict:
+    """검토 표시를 켜고 끈다 (value=None이면 지움). 내용 변경이 아니므로 rev를 올리지 않는다."""
+    out: dict = {}
+
+    def mutate(data: dict) -> dict:
+        case = _find(data, case_id)
+        flags = dict(case.get("flags", {}))
+        if value is None:
+            flags.pop(name, None)
+        else:
+            flags[name] = value
+        case["flags"] = flags
         out["case"] = dict(case)
         return data
 
     update_state(_cases_path(suite), mutate)
     return out["case"]
+
+
+def replace_source_version(suite: str, case_id: str, old_ref: str, new_ref: str) -> dict:
+    """출처의 버전 부분만 바꾼다: "conf:1@v14#§2" → "conf:1@v15#§2" (섹션 앵커는 유지)."""
+    out: dict = {}
+
+    def mutate(data: dict) -> dict:
+        case = _find(data, case_id)
+        case["source_refs"] = [new_ref + r[len(old_ref):] if r.startswith(old_ref) else r
+                               for r in case["source_refs"]]
+        out["case"] = dict(case)
+        return data
+
+    update_state(_cases_path(suite), mutate)
+    return out["case"]
```

- [ ] **Step 4: 추적 모듈** — `scripts/_tc_source_watch.py`

```python
"""출처 버전 변경 추적 (PRD F5.9, 로드맵 C6).

scan(suite): 라이브러리 케이스의 conf·figma 출처마다 현재 원격 버전을 한 번씩 확인하고,
            바뀌었으면 해당 케이스에 flags.source_change = {ref, from, to, at}을 단다.
ack(suite, case_id): 새 버전을 확인했다고 표시 — 출처 버전을 새 값으로 바꾸고 표시를 지운다.
diff(ref): 번들에 남은 옛 본문과 현재 원격 본문의 차이 (줄 단위).
원격 호출은 사용자가 "출처 변경 확인"을 누를 때만 한다 (라이브러리를 열 때마다 부르지 않는다).
"""
from __future__ import annotations

import difflib

from _tc_connectors import current_version, ref_base, refetch_markdown
from _tc_fetch import FetchError
from _tc_library import get_case, load_cases, replace_source_version, set_flag
from _tc_model import now_iso
from _tc_sources import find_source, read_text

WATCHED = ("conf", "figma")


def _versioned(ref: str) -> str:
    return ref.split("#", 1)[0]                     # "conf:1@v14#§2" → "conf:1@v14"


def scan(suite: str) -> dict:
    groups: dict[str, set[str]] = {}
    for case in load_cases(suite):
        for ref in case["source_refs"]:
            if ref.split(":", 1)[0] in WATCHED and "@" in ref:
                groups.setdefault(_versioned(ref), set()).add(case["case_id"])
    changes, errors = [], []
    for versioned, case_ids in sorted(groups.items()):
        old = versioned.split("@", 1)[1]
        try:
            new = current_version(versioned)
        except FetchError as exc:
            errors.append({"ref": versioned, "error": str(exc), "code": exc.code})
            continue
        if new and new != old:
            to_ref = f"{ref_base(versioned)}@{new}"
            for case_id in sorted(case_ids):
                set_flag(suite, case_id, "source_change",
                         {"ref": versioned, "from": old, "to": new, "to_ref": to_ref, "at": now_iso()})
            changes.append({"ref": versioned, "from": old, "to": new, "case_ids": sorted(case_ids)})
    return {"checked": len(groups), "changes": changes, "errors": errors}


def flagged(suite: str) -> list[dict]:
    """원격 호출 없이 지금 표시된 변경 목록 (배너용)."""
    out: dict[str, dict] = {}
    for case in load_cases(suite):
        change = case.get("flags", {}).get("source_change")
        if change:
            item = out.setdefault(change["ref"], {**{k: change[k] for k in ("ref", "from", "to")}, "case_ids": []})
            item["case_ids"].append(case["case_id"])
    return list(out.values())


def ack(suite: str, case_id: str) -> dict:
    case = get_case(suite, case_id)
    change = case.get("flags", {}).get("source_change")
    if not change:
        return case
    replace_source_version(suite, case_id, change["ref"], change["to_ref"])
    return set_flag(suite, case_id, "source_change", None)


def diff(ref: str, *, context: int = 1) -> dict:
    """옛 번들 본문(ref 버전) ↔ 현재 원격 본문. {old_available, lines:[{op:' '|'-'|'+', text}]}"""
    versioned = _versioned(ref)
    found = find_source(versioned)
    new_lines = refetch_markdown(versioned).splitlines()
    if not found:
        return {"old_available": False, "lines": [{"op": "+", "text": t} for t in new_lines[:200]]}
    bundle_id, entry = found
    old_lines = read_text(bundle_id, entry["source_id"]).splitlines()
    lines = []
    for line in difflib.unified_diff(old_lines, new_lines, lineterm="", n=context):
        if line.startswith(("---", "+++")):
            continue
        if line.startswith("@@"):
            lines.append({"op": "@", "text": "…"})
        else:
            lines.append({"op": line[0], "text": line[1:]})
    return {"old_available": True, "lines": lines[:400]}
```

- [ ] **Step 5: 통과 확인 + 회귀**

Run: `.venv/bin/python -m pytest tests/unit/tc_library -q -k "not e2e"`
Expected: 모두 통과

- [ ] **Step 6: 커밋**

```bash
git add scripts/_tc_model.py scripts/_tc_library.py scripts/_tc_source_watch.py tests/unit/tc_library/test_tc_source_watch.py
git commit -m "feat(tc-studio): C4 출처 버전 변경 추적·차이·확인 완료"
```

---

## Task C5: 원격 소스·자격증명·출처 변경 API

**Files:**
- Create: `agents/dashboard/routes_tc_connectors.py`
- Modify: `agents/dashboard/routes_tc_library.py` (아래 diff), `agents/dashboard/serve.py`
- Test: `tests/unit/tc_library/test_tc_connectors_api.py`

**Interfaces:**

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/tc-library/credentials` | 연결 상태 (토큰 없음) |
| PUT | `/api/tc-library/credentials/{confluence\|figma}` | 저장 → 연결 상태 |
| POST | `/api/tc-library/sources/{bundle}/url` | `{url}` → 201 `{source}` |
| POST | `/api/tc-library/sources/{bundle}/confluence` | `{url, children}` → 201 `{sources}` |
| POST | `/api/tc-library/sources/{bundle}/figma` | `{url}` → 201 `{source}` |
| GET | `/api/tc-library/sources/{bundle}/assets/{name}` | Figma 프레임 PNG |
| GET | `/api/tc-library/source-diff?ref=` | 차이 |
| POST | `/api/tc-library/{suite}/source-changes/scan` | 원격 버전 확인 → 표시 |
| GET | `/api/tc-library/{suite}/source-changes` | 표시된 변경 (원격 호출 없음) |
| POST | `/api/tc-library/{suite}/cases/{id}/ack-source` | 확인 완료 |

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/unit/tc_library/test_tc_connectors_api.py`

```python
from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from urllib.parse import quote

import pytest

from tests.unit.import_studio.import_studio_test_support import dashboard_server, request_json
from tests.unit.tc_library.connector_fixtures import (
    CLOUD, FIGMA_URL, PAGE_ID, STORAGE_V15, setup_confluence, setup_figma,
)
from tests.unit.tc_library.tc_fixtures import build_template_workbook
from tests.unit.tc_library.test_tc_library_api import _post_bytes

S = quote("야핏무브")


@pytest.fixture
def api(tmp_path: Path, fake_web):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    with dashboard_server(project) as base_url:
        xlsx = build_template_workbook(tmp_path / "src.xlsx").read_bytes()
        _, preview = _post_bytes(base_url, "/api/tc-library/import/preview?filename=a.xlsx", xlsx)
        request_json(base_url, "POST", "/api/tc-library/import", {
            "preview_id": preview["preview_id"], "suite": "야핏무브", "sheets": ["혜택"], "prefixes": {"혜택": "BEN"}})
        bundle = request_json(base_url, "POST", "/api/tc-library/sources")[1]["bundle_id"]
        yield base_url, bundle, fake_web


def test_credentials_never_return_tokens(api):
    base_url, _, _ = api
    status, body = request_json(base_url, "PUT", "/api/tc-library/credentials/confluence",
                                {"base_url": CLOUD, "email": "qa.lead@yafit.com", "token": "secret-token"})
    assert status == 200 and body["confluence"]["configured"] is True
    got = request_json(base_url, "GET", "/api/tc-library/credentials")[1]
    assert "secret-token" not in json.dumps(got) and got["confluence"]["email_masked"] == "qa****@yafit.com"
    assert request_json(base_url, "PUT", "/api/tc-library/credentials/slack", {})[0] == 404


def test_remote_sources_and_assets(api):
    base_url, bundle, web = api
    setup_confluence(web)
    setup_figma(web)
    web.add("https://docs.example.com/prd", "<h1>PRD</h1><p>본문</p>", headers={"Content-Type": "text/html"})
    web.private.add("internal.example")

    status, body = request_json(base_url, "POST", f"/api/tc-library/sources/{bundle}/url", {"url": "https://docs.example.com/prd"})
    assert (status, body["source"]["kind"]) == (201, "url")
    status, body = request_json(base_url, "POST", f"/api/tc-library/sources/{bundle}/url", {"url": "https://internal.example/x"})
    assert (status, body["code"]) == (400, "PRIVATE_ADDRESS")
    status, body = request_json(base_url, "POST", f"/api/tc-library/sources/{bundle}/confluence",
                                {"url": f"{CLOUD}/wiki/spaces/MOVE/pages/{PAGE_ID}/T"})
    assert (status, body["sources"][0]["ref"]) == (201, f"conf:{PAGE_ID}@v14")
    status, body = request_json(base_url, "POST", f"/api/tc-library/sources/{bundle}/figma", {"url": FIGMA_URL})
    asset = body["source"]["assets"][0]
    with urllib.request.urlopen(f"{base_url}/api/tc-library/sources/{bundle}/assets/{quote(asset)}", timeout=10) as resp:
        assert resp.headers["Content-Type"] == "image/png" and resp.read(4) == b"\x89PNG"
    assert request_json(base_url, "GET", f"/api/tc-library/sources/{bundle}/assets/..%2Fmanifest.json")[0] == 400


def test_source_changes_scan_list_diff_ack(api):
    base_url, bundle, web = api
    setup_confluence(web)
    request_json(base_url, "POST", f"/api/tc-library/sources/{bundle}/confluence", {"url": f"{CLOUD}/wiki/spaces/MOVE/pages/{PAGE_ID}"})
    import _tc_library as lib
    lib.add_source_refs("야핏무브", "BEN_0002", [f"conf:{PAGE_ID}@v14#§2"])

    setup_confluence(web, version=15, storage=STORAGE_V15)
    scan = request_json(base_url, "POST", f"/api/tc-library/{S}/source-changes/scan")[1]
    assert scan["changes"][0]["case_ids"] == ["BEN_0002"]
    assert request_json(base_url, "GET", f"/api/tc-library/{S}/source-changes")[1]["changes"][0]["to"] == "v15"
    listing = request_json(base_url, "GET", f"/api/tc-library/{S}?needs_review=1")[1]
    assert [c["case_id"] for c in listing["items"]] == ["BEN_0002"]
    diff = request_json(base_url, "GET", "/api/tc-library/source-diff?ref=" + quote(f"conf:{PAGE_ID}@v14#§2"))[1]
    assert any(line["op"] == "+" and "5초마다" in line["text"] for line in diff["lines"])
    case = request_json(base_url, "POST", f"/api/tc-library/{S}/cases/BEN_0002/ack-source")[1]["case"]
    assert "source_change" not in case["flags"]
    assert request_json(base_url, "GET", f"/api/tc-library/{S}/source-changes")[1]["changes"] == []
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_connectors_api.py -q`
Expected: FAIL — `GET /api/tc-library/credentials`가 스위트 조회로 잡혀 400 `INVALID_SUITE` (C4에서 `credentials`를 예약어로 막아 둔 상태)

- [ ] **Step 3: 라우트 Mixin** — `agents/dashboard/routes_tc_connectors.py`

```python
"""routes_tc_connectors.py — TC 스튜디오 원격 소스·자격증명·출처 변경 API (PRD F1.3, F1.4, F5.9, §7).

라우트 표는 routes_tc_library.ROUTES 맨 앞에 붙는다.
자격증명 응답에는 토큰이 절대 들어가지 않는다 (_tc_credentials.status()).
"""
from __future__ import annotations

import re

from dash_http import _read_body

_SUITE = r"(?P<suite>[^/]+)"
_CASE = r"(?P<case_id>[\w-]+)"
_BUNDLE = r"(?P<bundle_id>src_[0-9a-f]{12})"

CONNECTOR_ROUTES: list[tuple[str, re.Pattern, str]] = [
    (m, re.compile(p + r"\Z"), h) for m, p, h in [
        ("GET", r"/api/tc-library/credentials", "_tcc_credentials"),
        ("PUT", r"/api/tc-library/credentials/(?P<kind>confluence|figma)", "_tcc_save_credentials"),
        ("POST", rf"/api/tc-library/sources/{_BUNDLE}/url", "_tcc_add_url"),
        ("POST", rf"/api/tc-library/sources/{_BUNDLE}/confluence", "_tcc_add_confluence"),
        ("POST", rf"/api/tc-library/sources/{_BUNDLE}/figma", "_tcc_add_figma"),
        ("GET", rf"/api/tc-library/sources/{_BUNDLE}/assets/(?P<name>[^/]+)", "_tcc_asset"),
        ("GET", r"/api/tc-library/source-diff", "_tcc_diff"),
        ("POST", rf"/api/tc-library/{_SUITE}/source-changes/scan", "_tcc_scan"),
        ("GET", rf"/api/tc-library/{_SUITE}/source-changes", "_tcc_flagged"),
        ("POST", rf"/api/tc-library/{_SUITE}/cases/{_CASE}/ack-source", "_tcc_ack"),
    ]
]


class TcConnectorRoutesMixin:
    """_tcl_dispatch가 부른다. 응답은 TcLibraryRoutesMixin의 _tcl_json을 쓴다."""

    def _tcc_credentials(self):
        from _tc_credentials import status
        self._tcl_json({"ok": True, **status()})

    def _tcc_save_credentials(self, kind: str):
        from _tc_credentials import save
        self._tcl_json({"ok": True, **save(kind, _read_body(self))})

    def _tcc_add_url(self, bundle_id: str):
        from _tc_connectors import add_url
        body = _read_body(self)
        self._tcl_json({"ok": True, "source": add_url(bundle_id, str(body.get("url", "")).strip())}, 201)

    def _tcc_add_confluence(self, bundle_id: str):
        from _tc_connectors import add_confluence
        body = _read_body(self)
        entries = add_confluence(bundle_id, str(body.get("url", "")).strip(), children=bool(body.get("children")))
        self._tcl_json({"ok": True, "sources": entries}, 201)

    def _tcc_add_figma(self, bundle_id: str):
        from _tc_connectors import add_figma
        body = _read_body(self)
        self._tcl_json({"ok": True, "source": add_figma(bundle_id, str(body.get("url", "")).strip())}, 201)

    def _tcc_asset(self, bundle_id: str, name: str):
        from urllib.parse import unquote
        from _tc_sources import asset_path
        content = asset_path(bundle_id, unquote(name)).read_bytes()
        self._serve_bytes(content, "image/png")

    def _tcc_diff(self):
        from _tc_source_watch import diff
        self._tcl_json({"ok": True, **diff(self._tcl_query.get("ref", ""))})

    def _tcc_scan(self, suite: str):
        from _tc_library import suite_dir
        from _tc_source_watch import scan
        suite_dir(suite)
        self._tcl_json({"ok": True, **scan(suite)})

    def _tcc_flagged(self, suite: str):
        from _tc_source_watch import flagged
        self._tcl_json({"ok": True, "changes": flagged(suite)})

    def _tcc_ack(self, suite: str, case_id: str):
        from _tc_library import with_issues
        from _tc_source_watch import ack
        self._tcl_json({"ok": True, "case": with_issues(ack(suite, case_id))})
```

- [ ] **Step 4: 라우트 표 결합**

```diff
--- a/agents/dashboard/routes_tc_library.py
+++ b/agents/dashboard/routes_tc_library.py
@@ -46,8 +46,9 @@
 
 # 생성·검토 라우트(Phase 2)가 앞에 와야 `/api/tc-library/{suite}` 패턴에 먼저 잡히지 않는다
 from routes_tc_authoring import AUTHORING_ROUTES  # noqa: E402
+from routes_tc_connectors import CONNECTOR_ROUTES  # noqa: E402  (Phase 3)
 
-ROUTES[:0] = AUTHORING_ROUTES
+ROUTES[:0] = CONNECTOR_ROUTES + AUTHORING_ROUTES
 
 
 class TcLibraryRoutesMixin:
```

- [ ] **Step 5: serve.py** — `from routes_tc_authoring import …` 줄 아래에 `from routes_tc_connectors import TcConnectorRoutesMixin            # TC 스튜디오 원격 소스`, 클래스 상속의 `TcAuthoringRoutesMixin,` 아래에 `TcConnectorRoutesMixin,`

- [ ] **Step 6: 통과 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library -q -k "not e2e"`
Expected: 모두 통과 (Phase 1·2 포함)

- [ ] **Step 7: 커밋**

```bash
git add agents/dashboard/routes_tc_connectors.py agents/dashboard/routes_tc_library.py agents/dashboard/serve.py tests/unit/tc_library/test_tc_connectors_api.py
git commit -m "feat(tc-studio): C5 원격 소스·자격증명·출처 변경 API"
```

---

## Task W9: 원격 소스 탭 · 연결 설정 · Figma 프레임

**Files:**
- Create: `agents/dashboard/static/js/tc-studio/connectors.js`
- Modify: `api.js`, `generate.js`, `review.js` (아래 diff)
- Modify: `agents/dashboard/index.html` (`generate.js` 줄 아래에 `connectors.js`)
- Test: `tests/unit/tc_library/test_tc_connectors_e2e.py`

**Interfaces:**
- Produces: 소스 탭 `src-tab-url` `src-tab-confluence` `src-tab-figma`, 입력 `src-{url|confluence|figma}-url`·`-fetch`, `src-confluence-children`, 연결 상태 `cred-status-confluence` `cred-status-figma` `cred-settings`, 설정 창 `cred-modal` `cred-base` `cred-email` `cred-deployment` `cred-conf-token` `cred-figma-token` `cred-save` `cred-cancel` `cred-close`, 검토 원문의 `source-figma-frame`
- `TCS_NS.sourceWatch.{renderBanner, scan, detailSource, figmaFrames}` (W10이 라이브러리·상세에 붙인다)
- `TCS_NS.generateView.{ensureBundle, pushSource}` (Confluence 여러 페이지를 한 번에 넣을 때)

- [ ] **Step 1: 실패하는 E2E 테스트 작성** — `tests/unit/tc_library/test_tc_connectors_e2e.py` (W10 절은 뒤에서)

```python
"""TC 스튜디오 원격 소스·연결 설정·출처 변경 화면 (Phase 3 W9·W10). 네트워크 대신 fake_web을 쓴다."""
from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

import _tc_library as lib
from tests.unit.import_studio.import_studio_test_support import dashboard_server
from tests.unit.tc_library.connector_fixtures import (
    CLOUD, FIGMA_URL, PAGE_ID, STORAGE_V15, setup_confluence, setup_figma,
)
from tests.unit.tc_library.test_tc_studio_e2e import _seed


@pytest.fixture
def studio(tmp_path: Path, page: Page, fake_web, fake_claude):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    with dashboard_server(project) as base_url:
        _seed(base_url, tmp_path)
        page.goto(base_url + "/tc-studio")
        expect(page.locator("#grid-body tr[data-case]")).to_have_count(6)
        yield base_url, page, fake_web


def _open_tab(page: Page, tab: str) -> None:
    page.locator('[data-id="nav-tab-generate"]').click()
    page.locator(f'[data-id="src-tab-{tab}"]').click()


# ── W9: 원격 소스 탭 · 연결 설정 ────────────────────────────────
def test_settings_modal_saves_without_showing_token(studio):
    _, page, web = studio
    page.locator('[data-id="nav-tab-generate"]').click()
    expect(page.locator('[data-id="cred-status-confluence"]')).to_have_text("Confluence 미연결")
    page.locator('[data-id="cred-settings"]').click()
    page.locator('[data-id="cred-base"]').fill(CLOUD)
    page.locator('[data-id="cred-email"]').fill("qa.lead@yafit.com")
    page.locator('[data-id="cred-conf-token"]').fill("secret-token")
    page.locator('[data-id="cred-save"]').click()
    expect(page.locator('[data-id="cred-status-confluence"]')).to_have_text("Confluence 연결됨 · qa****@yafit.com")
    assert "secret-token" not in page.content()


def test_confluence_url_and_figma_sources(studio):
    _, page, web = studio
    setup_confluence(web)
    setup_figma(web)
    web.add("https://docs.example.com/prd", "<title>PRD</title><h1>배너</h1><p>본문</p>", headers={"Content-Type": "text/html"})
    page.reload()
    _open_tab(page, "confluence")
    page.locator('[data-id="src-confluence-url"]').fill(f"{CLOUD}/wiki/spaces/MOVE/pages/{PAGE_ID}/T")
    page.locator('[data-id="src-confluence-fetch"]').click()
    expect(page.locator('[data-id="src-chip"]')).to_have_count(1)
    expect(page.locator('[data-id="src-chip"] .src-ref').first).to_have_text(f"conf:{PAGE_ID}@v14")
    page.locator('[data-id="src-tab-figma"]').click()
    page.locator('[data-id="src-figma-url"]').fill(FIGMA_URL)
    page.locator('[data-id="src-figma-fetch"]').click()
    page.locator('[data-id="src-tab-url"]').click()
    page.locator('[data-id="src-url-url"]').fill("https://docs.example.com/prd")
    page.locator('[data-id="src-url-fetch"]').click()
    expect(page.locator('[data-id="src-chip"]')).to_have_count(3)


def test_figma_draft_shows_frame_in_review(studio):
    _, page, web = studio
    setup_figma(web)
    page.reload()
    _open_tab(page, "figma")
    page.locator('[data-id="src-figma-url"]').fill(FIGMA_URL)
    page.locator('[data-id="src-figma-fetch"]').click()
    expect(page.locator('[data-id="src-chip"]')).to_have_count(1)
    page.locator('[data-id="gen-path-l2"]').select_option("상단 배너")
    page.locator('[data-id="gen-submit"]').click()
    page.locator('[data-id="job-open-review"]').click(timeout=15000)
    expect(page.locator('[data-id="source-figma-frame"] img')).to_have_count(1)
    expect(page.locator('[data-id="draft-card"]').first).not_to_contain_text("추정")
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_connectors_e2e.py -q`
Expected: FAIL — `cred-status-confluence`를 찾지 못함

- [ ] **Step 3: API 클라이언트·생성·검토 화면 수정**

```diff
--- a/agents/dashboard/static/js/tc-studio/api.js
+++ b/agents/dashboard/static/js/tc-studio/api.js
@@ -67,5 +67,16 @@
       request('GET', `${S(suite)}/coverage?${new URLSearchParams({ sheet, path: path.join('/'), profile })}`),
     resolveDuplicate: (suite, id, payload) => request('POST', `${C(suite, id)}/resolve-duplicate`, payload),
     mappingProfiles: () => request('GET', '/api/tc-library/import/mapping-profiles'),
+    // ── Phase 3: 원격 소스·자격증명·출처 변경 ──
+    addSourceUrl: (bundleId, url) => request('POST', `/api/tc-library/sources/${enc(bundleId)}/url`, { url }),
+    addSourceConfluence: (bundleId, url, children) =>
+      request('POST', `/api/tc-library/sources/${enc(bundleId)}/confluence`, { url, children }),
+    addSourceFigma: (bundleId, url) => request('POST', `/api/tc-library/sources/${enc(bundleId)}/figma`, { url }),
+    credentials: () => request('GET', '/api/tc-library/credentials'),
+    saveCredentials: (kind, fields) => request('PUT', `/api/tc-library/credentials/${enc(kind)}`, fields),
+    sourceChanges: (suite) => request('GET', `${S(suite)}/source-changes`),
+    scanSources: (suite) => request('POST', `${S(suite)}/source-changes/scan`),
+    sourceDiff: (ref) => request('GET', `/api/tc-library/source-diff?ref=${enc(ref)}`),
+    ackSource: (suite, id) => request('POST', `${C(suite, id)}/ack-source`),
   };
 })(window.TCS_NS = window.TCS_NS || {});
```

```diff
--- a/agents/dashboard/static/js/tc-studio/generate.js
+++ b/agents/dashboard/static/js/tc-studio/generate.js
@@ -137,6 +137,8 @@
     }
   }
   NS.generateView.addSource = addSource;
+  NS.generateView.ensureBundle = ensureBundle;
+  NS.generateView.pushSource = (source) => { bundle.sources.push(source); renderSources(); };   // Phase 3 (Confluence 여러 페이지)
 
   function renderSources() {
     $('#srcs', root).innerHTML = bundle.sources.map((s) => `<div class="src-card" data-id="src-chip">
```

```diff
--- a/agents/dashboard/static/js/tc-studio/review.js
+++ b/agents/dashboard/static/js/tc-studio/review.js
@@ -7,6 +7,7 @@
   let drafts = [];          // 이번 검토 대상 (작업 id가 있으면 그 작업의 초안 전부, 없으면 draft 상태 전부)
   let targets = {};         // 중복 후보 case_id → 케이스
   let jobInfo = null;
+  let manifest = null;      // 작업 소스 묶음 (Figma 프레임 이미지용, Phase 3)
   let focus = 0;
   let filter = 'all';
 
@@ -55,6 +56,7 @@
     const query = state.reviewJob ? { job: state.reviewJob, limit: 1000 } : { status: 'draft', limit: 1000 };
     drafts = (await api.list(state.suite, query)).items;
     jobInfo = state.reviewJob ? await api.job(state.reviewJob).catch(() => null) : null;
+    manifest = jobInfo ? await api.bundle(jobInfo.job.bundle_id).catch(() => null) : null;
     const ids = [...new Set(drafts.flatMap((d) => (d.draft_meta.duplicates || []).map((h) => h.case_id)))];
     targets = {};
     await Promise.all(ids.map(async (id) => { targets[id] = (await api.getCase(state.suite, id)).case; }));
@@ -197,7 +199,9 @@
       let text = esc(ex.markdown);
       const quote = d.draft_meta.source_quote && esc(d.draft_meta.source_quote);
       if (quote && text.includes(quote)) text = text.replace(quote, `<mark>${quote}</mark>`);
-      box.innerHTML = `<h5>${esc(ex.title)} › ${esc(ex.section)} (${esc(ex.anchor)})</h5><div style="white-space:pre-wrap">${text}</div>`;
+      const entry = manifest && manifest.sources.find((s) => ref.startsWith(s.ref));
+      const frames = NS.sourceWatch && entry ? NS.sourceWatch.figmaFrames(jobInfo.job.bundle_id, entry) : '';
+      box.innerHTML = `<h5>${esc(ex.title)} › ${esc(ex.section)} (${esc(ex.anchor)})</h5>${frames}<div style="white-space:pre-wrap">${text}</div>`;
     } catch (err) {
       box.innerHTML = `<span class="faint">원문을 불러오지 못했습니다: ${esc(err.message)}</span>`;
     }
```

- [ ] **Step 4: 원격 소스 모듈** — `agents/dashboard/static/js/tc-studio/connectors.js`

목업의 PRD URL·Confluence·Figma 탭(596~617행)과 연결 상태(618~622행)를 옮기고, 목업에 없던 연결 설정 창을 더했다. `generate.js` 다음, `review.js`·`main.js` 전에 로드해야 탭이 등록된다.

```javascript
// TC 스튜디오 — 원격 소스(PRD URL·Confluence·Figma) 탭, 연결 설정, 출처 변경 배너 (PRD F1.3, F1.4, F5.9, §7)
// generate.js의 registerSourceTab()과 library.js의 sourceWatch 훅에 붙는다. generate.js 다음, main.js 전에 로드.
(function (NS) {
  'use strict';

  const { state, api, esc, $, $$, toast } = NS;
  let creds = { confluence: { configured: false }, figma: { configured: false } };

  function urlTab(id, label, placeholder, help, run, extra = '') {
    NS.generateView.registerSourceTab({
      id, label,
      html: () => `<div class="field"><div class="row" style="flex-wrap:nowrap">
          <input class="input" id="src-${id}-url" data-id="src-${id}-url" placeholder="${esc(placeholder)}" autocomplete="off" aria-label="${esc(label)} 주소">
          <button class="btn btn-ghost" data-id="src-${id}-fetch" id="src-${id}-fetch">수집</button></div>
        ${extra}<span class="help">${help}</span></div>`,
      mount: (r, add) => {
        const input = $(`#src-${id}-url`, r);
        const go = async () => {
          const url = input.value.trim();
          if (!/^https?:\/\//.test(url)) { input.classList.add('error'); toast('주소를 https://로 시작하게 넣어 주세요.', 'err'); return; }
          input.classList.remove('error');
          const btn = $(`#src-${id}-fetch`, r);
          btn.classList.add('loading');
          btn.disabled = true;
          try {
            if (await run(add, url, r)) input.value = '';
          } finally {
            btn.classList.remove('loading');
            btn.disabled = false;
          }
        };
        $(`#src-${id}-fetch`, r).addEventListener('click', go);
        input.addEventListener('keydown', (e) => { if (e.key === 'Enter') go(); });
      },
    });
  }

  urlTab('url', 'PRD URL', 'https://docs.example.com/product/prd 또는 PDF 문서 주소',
    '공개 HTTPS 문서(HTML·PDF·DOCX·Markdown·텍스트). 로그인이 필요한 문서는 Confluence 연결이나 파일 업로드를 쓰세요. 내부망 주소는 막습니다.',
    (add, url) => add((id) => api.addSourceUrl(id, url)));

  urlTab('confluence', 'Confluence', 'https://회사.atlassian.net/wiki/spaces/…/pages/48213377/…',
    'Cloud: /wiki/spaces/…/pages/{id}, viewpage.action?pageId=, /x/{tiny} · Server/DC: 연결 설정에서 base URL 지정',
    async (add, url, r) => {
      if (!creds.confluence.configured) { openSettings('confluence'); return false; }
      const children = $('#src-confluence-children', r).checked;
      try {
        const id = await NS.generateView.ensureBundle();
        const { sources } = await api.addSourceConfluence(id, url, children);
        sources.forEach((s) => NS.generateView.pushSource(s));
        toast(`Confluence 페이지 ${sources.length}개를 가져왔습니다 (${esc(sources[0].version)})`, 'ok', [], 2500);
        return true;
      } catch (err) {
        toast(`가져오지 못했습니다: ${esc(err.message)}`, 'err');
        return false;
      }
    },
    '<label class="row help"><input type="checkbox" id="src-confluence-children" data-id="src-confluence-children"> 하위 페이지 포함 (깊이 1, 최대 20개)</label>');

  urlTab('figma', 'Figma', 'https://www.figma.com/design/{fileKey}/…?node-id=12-345',
    'node-id가 있으면 그 프레임만, 없으면 상위 프레임 최대 10개. 화면 문구는 "확인된 문구"로 들어갑니다.',
    async (add, url) => {
      if (!creds.figma.configured) { openSettings('figma'); return false; }
      return add((id) => api.addSourceFigma(id, url));
    });

  // ── 연결 상태 · 설정 ─────────────────────────────────────────
  function credHtml() {
    const c = creds.confluence;
    return `<span class="tag ${c.configured ? 'ok' : ''}" data-id="cred-status-confluence">${c.configured ? `Confluence 연결됨 · ${esc(c.email_masked || c.base_url)}` : 'Confluence 미연결'}</span>
      <span class="tag ${creds.figma.configured ? 'ok' : ''}" data-id="cred-status-figma">${creds.figma.configured ? 'Figma 연결됨' : 'Figma 미연결'}</span>
      <button class="btn-sm" data-id="cred-settings" id="cred-settings">연결 설정</button>`;
  }

  async function loadCreds() {
    creds = await api.credentials();
    const box = $('#src-extra');
    if (!box) return;
    box.innerHTML = `<div class="cred">${credHtml()}</div>`;
    $('#cred-settings', box).addEventListener('click', () => openSettings('confluence'));
  }

  function openSettings(kind) {
    const scrim = $('#cred-modal');
    const c = creds.confluence;
    $('#cred-base', scrim).value = c.base_url || '';
    $('#cred-email', scrim).value = '';
    $('#cred-email', scrim).placeholder = c.email_masked || 'qa@회사.com';
    $('#cred-deployment', scrim).value = c.deployment || 'cloud';
    $('#cred-conf-token', scrim).value = '';
    $('#cred-figma-token', scrim).value = '';
    scrim.hidden = false;
    $(kind === 'figma' ? '#cred-figma-token' : '#cred-base', scrim).focus();
  }

  function modalHtml() {
    return `<div class="scrim" id="cred-modal" data-id="cred-modal" hidden>
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="cred-title" style="width:min(480px,100%)">
        <div class="panel-head"><span id="cred-title">연결 설정</span><span class="spacer"></span><button class="icon-btn" data-id="cred-close" id="cred-close" aria-label="닫기">✕</button></div>
        <div class="panel-body" style="display:grid;gap:10px">
          <b>Confluence</b>
          <label class="field">base URL<input class="input" id="cred-base" data-id="cred-base" placeholder="https://회사.atlassian.net"></label>
          <div class="row"><label class="field" style="flex:1">이메일 (Cloud)<input class="input" id="cred-email" data-id="cred-email"></label>
            <label class="field">배포<select class="select" id="cred-deployment" data-id="cred-deployment"><option value="cloud">Cloud (이메일+API 토큰)</option><option value="dc">Server/DC (개인 액세스 토큰)</option></select></label></div>
          <label class="field">토큰<input class="input" type="password" id="cred-conf-token" data-id="cred-conf-token" placeholder="비워 두면 기존 토큰 유지" autocomplete="off"></label>
          <b>Figma</b>
          <label class="field">개인 액세스 토큰<input class="input" type="password" id="cred-figma-token" data-id="cred-figma-token" placeholder="비워 두면 기존 토큰 유지" autocomplete="off"></label>
          <span class="help">토큰은 서버의 config/*_config.json(git 제외)에만 저장되고 다시 보여 주지 않습니다.</span>
          <div class="row"><span class="spacer"></span><button class="btn btn-ghost" id="cred-cancel" data-id="cred-cancel">취소</button><button class="btn btn-primary" id="cred-save" data-id="cred-save">저장</button></div>
        </div></div></div>`;
  }

  async function saveSettings() {
    const scrim = $('#cred-modal');
    try {
      const base = $('#cred-base', scrim).value.trim();
      const email = $('#cred-email', scrim).value.trim();
      const confToken = $('#cred-conf-token', scrim).value.trim();
      if (base || email || confToken) {
        await api.saveCredentials('confluence', { base_url: base, deployment: $('#cred-deployment', scrim).value,
          ...(email ? { email } : {}), token: confToken });
      }
      const figmaToken = $('#cred-figma-token', scrim).value.trim();
      if (figmaToken) await api.saveCredentials('figma', { token: figmaToken });
      scrim.hidden = true;
      toast('연결 설정을 저장했습니다.', 'ok');
      await loadCreds();
    } catch (err) {
      toast(`저장하지 못했습니다: ${esc(err.message)}`, 'err');
    }
  }

  // ── 출처 변경 배너 (라이브러리) ──────────────────────────────
  NS.sourceWatch = {
    async renderBanner(root) {
      const box = $('#lib-banners', root);
      if (!box || !state.suite) return;
      const { changes } = await api.sourceChanges(state.suite);
      const count = changes.reduce((n, c) => n + c.case_ids.length, 0);
      $('#n-review', root).textContent = count;
      box.innerHTML = changes.length ? `<div class="banner warn" data-id="banner-source-changed"><b>출처 문서가 바뀌었습니다</b>
        <span>${changes.map((c) => `${esc(c.ref.split('@')[0])} ${esc(c.from)} → ${esc(c.to)}`).join(' · ')} · 관련 케이스 ${count}건이 재검토 필요 상태입니다.</span>
        <span class="spacer"></span><button class="btn-sm" data-id="banner-review-now" id="banner-review-now">${count}건만 보기</button></div>` : '';
      const b = $('#banner-review-now', box);
      if (b) b.addEventListener('click', () => { const chip = $('#lib-filter-needs-review', root); if (chip.getAttribute('aria-pressed') !== 'true') chip.click(); });
    },
    async scan(root) {
      const btn = $('#btn-check-sources', root);
      btn.classList.add('loading');
      btn.disabled = true;
      try {
        const res = await api.scanSources(state.suite);
        const errs = res.errors.length ? ` · 확인 실패 ${res.errors.length}건 (${esc(res.errors[0].error)})` : '';
        toast(res.changes.length ? `출처 ${res.changes.length}개가 바뀌었습니다${errs}` : `출처 ${res.checked}개 모두 최신입니다${errs}`, res.changes.length || res.errors.length ? 'warn' : 'ok');
        await NS.library.refresh();
      } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
      }
    },
  };

  // 상세 패널 원문 탭: 바뀐 출처의 차이 + 확인 완료 (detail.js가 부른다)
  NS.sourceWatch.detailSource = async function (box, c, onAck) {
    const change = (c.flags || {}).source_change;
    if (!change) return;
    const ref = c.source_refs.find((r) => r.startsWith(change.ref)) || change.ref;
    box.insertAdjacentHTML('beforeend', `<div class="warnbox" data-id="detail-source-diff"><b>${esc(change.from)} → ${esc(change.to)}에서 바뀐 부분</b><div class="diff" id="d-diff">불러오는 중…</div>
      <div class="row"><button class="btn-sm" data-id="detail-mark-reviewed" id="detail-mark-reviewed">변경 확인 완료</button></div></div>`);
    $('#detail-mark-reviewed', box).addEventListener('click', onAck);
    try {
      const { lines, old_available: old } = await api.sourceDiff(ref);
      $('#d-diff', box).innerHTML = (old ? '' : '<div class="faint">옛 본문이 없어 새 본문만 보여 줍니다</div>')
        + lines.filter((l) => l.op !== ' ').slice(0, 60).map((l) => (l.op === '-' ? `<del>${esc(l.text)}</del>` : l.op === '+' ? `<ins>${esc(l.text)}</ins>` : '<span class="faint">…</span>')).join('<br>');
    } catch (err) {
      $('#d-diff', box).textContent = `차이를 불러오지 못했습니다: ${err.message}`;
    }
  };

  // 초안 검토 원문 패널: Figma 출처면 프레임 이미지 (review.js가 부른다)
  NS.sourceWatch.figmaFrames = function (bundleId, entry) {
    if (!entry || entry.kind !== 'figma' || !(entry.assets || []).length) return '';
    return `<div class="figma-shots" data-id="source-figma-frame">${entry.assets.map((a) =>
      `<img src="/api/tc-library/sources/${encodeURIComponent(bundleId)}/assets/${encodeURIComponent(a)}" alt="${esc(entry.title)} 프레임" style="max-width:100%;border-radius:12px;border:1px solid var(--line)">`).join('')}</div>`;
  };

  // generate 화면이 그려진 뒤 연결 상태와 설정 창을 붙인다
  const origMount = NS.generateView.mount;
  NS.generateView.mount = function (root) {
    origMount(root);
    root.querySelector('.tc-studio').insertAdjacentHTML('beforeend', modalHtml());
    const scrim = $('#cred-modal');
    ['#cred-close', '#cred-cancel'].forEach((s) => $(s, scrim).addEventListener('click', () => { scrim.hidden = true; }));
    $('#cred-save', scrim).addEventListener('click', saveSettings);
    loadCreds();
  };
})(window.TCS_NS = window.TCS_NS || {});
```

- [ ] **Step 5: 스크립트 연결** — index.html의 `tc-studio/generate.js` 줄 아래:

```html
  <script src="/static/js/tc-studio/connectors.js?v=20260930-2"></script>
```

- [ ] **Step 6: 통과 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_connectors_e2e.py -q`
Expected: `3 passed`

- [ ] **Step 7: 커밋**

```bash
git add agents/dashboard/static/js/tc-studio/connectors.js agents/dashboard/static/js/tc-studio/api.js agents/dashboard/static/js/tc-studio/generate.js agents/dashboard/static/js/tc-studio/review.js agents/dashboard/index.html tests/unit/tc_library/test_tc_connectors_e2e.py
git commit -m "feat(tc-studio): W9 원격 소스 탭·연결 설정·Figma 프레임"
```

---

## Task W10: 출처 변경 배너 · 재검토 필터 · 차이 · 확인 완료

PRD 범위: F5.9 · 목업 `banner-source-changed`, `lib-filter-needs-review`, 상세 원문 탭의 "변경 확인 완료"

**Files:**
- Modify: `state.js`, `library.js`, `detail.js` (아래 diff)
- Modify: `tests/unit/tc_library/test_tc_connectors_e2e.py` (파일 끝에 W10 절)

**Interfaces:**
- `data-id`: `btn-check-sources`(그리드 위 "출처 변경 확인"), `lib-banners`, `banner-source-changed`, `banner-review-now`, `lib-filter-needs-review`, `detail-source-diff`, `detail-mark-reviewed`
- 필터 `state.filters.needs_review` → `?needs_review=1`

- [ ] **Step 1: 실패하는 E2E 테스트 추가** — 파일 끝에:

```python
# ── W10: 출처 변경 배너 · 차이 · 확인 ───────────────────────────
def test_source_change_banner_diff_and_ack(studio):
    base_url, page, web = studio
    setup_confluence(web)
    import _tc_sources as src
    import _tc_connectors as conn
    conn.add_confluence(src.new_bundle(), f"{CLOUD}/wiki/spaces/MOVE/pages/{PAGE_ID}")
    lib.add_source_refs("야핏무브", "BEN_0002", [f"conf:{PAGE_ID}@v14#§2"])
    setup_confluence(web, version=15, storage=STORAGE_V15)
    page.reload()

    page.locator('[data-id="btn-check-sources"]').click()
    expect(page.locator('[data-id="banner-source-changed"]')).to_contain_text("v14 → v15")
    page.locator('[data-id="banner-review-now"]').click()
    expect(page.locator("#grid-body tr[data-case]")).to_have_count(1)
    page.locator('tr[data-case="BEN_0002"] td.no').click()
    page.locator('[data-id="detail-tab-source"]').click()
    expect(page.locator('[data-id="detail-source-diff"] ins')).to_contain_text("5초마다")
    page.locator('[data-id="detail-mark-reviewed"]').click()
    expect(page.locator('[data-id="banner-source-changed"]')).to_have_count(0)
    assert f"conf:{PAGE_ID}@v15#§2" in lib.get_case("야핏무브", "BEN_0002")["source_refs"]
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_connectors_e2e.py -k source_change -q`
Expected: FAIL — `btn-check-sources`를 찾지 못함

- [ ] **Step 3: 구현**

```diff
--- a/agents/dashboard/static/js/tc-studio/state.js
+++ b/agents/dashboard/static/js/tc-studio/state.js
@@ -9,7 +9,7 @@
     items: [],          // 현재 필터 결과 (서버 응답 그대로, issues 포함)
     total: 0,
     filters: { q: '', path: '', status: '', execution_result: '', priority: '', auto: '',
-               source: '', invalid: false },
+               source: '', invalid: false, needs_review: false },
     selected: new Set(),
     activeId: '',
     screen: 'library',
@@ -25,7 +25,7 @@
   NS.queryFromFilters = function (f) {
     const q = {};
     Object.entries(f).forEach(([k, v]) => {
-      if (k === 'invalid') { if (v) q.invalid = '1'; return; }
+      if (k === 'invalid' || k === 'needs_review') { if (v) q[k] = '1'; return; }
       if (k === 'execution_result') {
         if (v === 'none') q.execution_result = '';
         else if (v) q.execution_result = v;
```

```diff
--- a/agents/dashboard/static/js/tc-studio/library.js
+++ b/agents/dashboard/static/js/tc-studio/library.js
@@ -26,6 +26,7 @@
         <div class="tree-legend"><span><i class="dot d-draft"></i>초안</span><span><i class="dot d-review"></i>재검토</span><span><i class="dot d-err"></i>검증 오류</span></div>
       </aside>
       <div class="center">
+        <div id="lib-banners"></div>
         <div class="filterbar" role="search">
           <div class="search"><input class="input" id="lib-search" data-id="lib-search" placeholder="기능, Step, Expected, UI 문구 검색  ( / )" autocomplete="off"></div>
           <select class="fselect" id="lib-filter-result" data-id="lib-filter-result" aria-label="실행 결과">
@@ -38,6 +39,7 @@
             ${opt('', 'AUTO 전체')}${NS.AUTO_VALUES.map((a) => opt(a, a)).join('')}${opt('-', '미지정')}</select>
           <select class="fselect" id="lib-filter-source" data-id="lib-filter-source" aria-label="출처">
             ${opt('', '출처 전체')}${opt('xlsx', '엑셀 가져오기')}${opt('conf', 'Confluence')}${opt('figma', 'Figma')}${opt('file', '파일·붙여넣기')}</select>
+          ${NS.sourceWatch ? '<button class="fchip" data-id="lib-filter-needs-review" id="lib-filter-needs-review" aria-pressed="false">재검토 필요 <span class="n" id="n-review">0</span></button>' : ''}
           <button class="fchip" data-id="lib-filter-invalid" id="lib-filter-invalid" aria-pressed="false">검증 오류 <span class="n" id="n-invalid">0</span></button>
           <button class="btn-sm" data-id="lib-filter-reset" id="lib-filter-reset">초기화</button>
         </div>
@@ -46,6 +48,7 @@
           <span id="grid-count" class="num"></span>
           <span class="spacer"></span>
           <span class="faint">더블클릭 또는 Enter로 셀 편집 · <span class="kbd">⌘</span><span class="kbd">↵</span> 저장 · <span class="kbd">Esc</span> 취소</span>
+          ${NS.sourceWatch ? '<button class="btn btn-ghost" data-id="btn-check-sources" id="btn-check-sources" title="Confluence·Figma 출처의 새 버전을 확인합니다">출처 변경 확인</button>' : ''}
           <button class="btn btn-primary" data-id="btn-add-case" id="btn-add-case">+ 케이스 추가</button>
         </div>
         <div class="grid-wrap" id="grid-wrap">
@@ -118,6 +121,7 @@
     if (!open.size) tree.forEach((n) => { open.add(key(n.path)); (n.children || []).forEach((c) => open.add(key(c.path))); });
     renderTree();
     await reloadList();
+    if (NS.sourceWatch) await NS.sourceWatch.renderBanner(root);
   }
 
   async function reloadList() {
@@ -393,6 +397,15 @@
       clearTimeout(t);
       t = setTimeout(() => { state.filters.q = e.target.value.trim(); reloadList(); }, 250);
     });
+    if (NS.sourceWatch) {
+      $('#lib-filter-needs-review', root).addEventListener('click', (e) => {
+        const on = e.currentTarget.getAttribute('aria-pressed') !== 'true';
+        e.currentTarget.setAttribute('aria-pressed', on);
+        state.filters.needs_review = on;
+        reloadList();
+      });
+      $('#btn-check-sources', root).addEventListener('click', () => NS.sourceWatch.scan(root));
+    }
     $('#lib-filter-invalid', root).addEventListener('click', (e) => {
       const on = e.currentTarget.getAttribute('aria-pressed') !== 'true';
       e.currentTarget.setAttribute('aria-pressed', on);
@@ -400,7 +413,8 @@
       reloadList();
     });
     $('#lib-filter-reset', root).addEventListener('click', () => {
-      Object.keys(state.filters).forEach((k) => { state.filters[k] = k === 'invalid' ? false : ''; });
+      Object.keys(state.filters).forEach((k) => { state.filters[k] = ['invalid', 'needs_review'].includes(k) ? false : ''; });
+      $$('.fchip', root).forEach((b) => b.setAttribute('aria-pressed', 'false'));
       $$('.filterbar select', root).forEach((s) => { s.value = ''; });
       $('#lib-search', root).value = '';
       $('#lib-filter-invalid', root).setAttribute('aria-pressed', 'false');
```

```diff
--- a/agents/dashboard/static/js/tc-studio/detail.js
+++ b/agents/dashboard/static/js/tc-studio/detail.js
@@ -108,7 +108,8 @@
   function fill() {
     const c = draft;
     $('#d-id', root).textContent = c.case_id;
-    $('#d-status', root).innerHTML = `<span class="pill st-${current.status}">${NS.STATUS_LABEL[current.status]}</span>`;
+    $('#d-status', root).innerHTML = `<span class="pill st-${current.status}">${NS.STATUS_LABEL[current.status]}</span>`
+      + ((current.flags || {}).source_change ? ' <span class="pill st-needs_review">재검토 필요</span>' : '');
     $('#d-rev', root).textContent = `rev ${current.rev}`;
     $('#detail-feature', root).value = c.feature;
     $('#d-path', root).textContent = [c.sheet, ...c.path.filter(Boolean)].join(' › ');
@@ -128,7 +129,15 @@
     $('#d-checks', root).innerHTML = (current.issues.length ? current.issues : [{ level: 'ok', message: '문제 없음' }])
       .map((i) => `<li><span class="${i.level === 'error' ? 'bad' : i.level === 'warning' ? 'wr' : 'ok'}">${i.level === 'error' ? '✕' : i.level === 'warning' ? '!' : '✓'}</span>${esc(i.message)}</li>`).join('');
     $('#d-source', root).innerHTML = `<div class="excerpt"><h5>출처</h5>${c.source_refs.map((r) => `<div class="mono" style="font-size:11px">${esc(r)}</div>`).join('')}
-      <p class="faint" style="margin:8px 0 0">문서 원문 하이라이트는 문서 기반 생성(Phase 2)부터 표시됩니다. 엑셀에서 온 케이스는 가져온 파일·시트·행을 보여줍니다.</p></div>`;
+      <p class="faint" style="margin:8px 0 0">문서 원문 하이라이트는 초안 검토 화면에서 봅니다. 엑셀에서 온 케이스는 가져온 파일·시트·행을 보여줍니다.</p></div>`;
+    if (NS.sourceWatch) {
+      NS.sourceWatch.detailSource($('#d-source', root), current, async () => {
+        await api.ackSource(state.suite, current.case_id);
+        toast(`${current.case_id}의 출처를 새 버전으로 올리고 재검토를 해제했습니다.`, 'ok');
+        await NS.library.refresh();
+        await open(current.case_id, 'source');
+      });
+    }
     loadHistory();
     markDirty();
   }
```

- [ ] **Step 4: 통과 확인 + 전체 회귀 + 반복**

Run: `.venv/bin/python -m pytest tests/unit/tc_library -q`
Expected: `99 passed`

Run: `.venv/bin/python -m pytest -q`
Expected: `776 passed, 1 skipped` (기존 677 + TC 스튜디오 99)

Run: `for i in 1 2 3; do .venv/bin/python -m pytest tests/unit/tc_library -q | tail -1; done`
Expected: 3번 모두 통과 (E2E가 흔들리면 결함으로 보고 조사한다)

- [ ] **Step 5: 커밋**

```bash
git add agents/dashboard/static/js/tc-studio/state.js agents/dashboard/static/js/tc-studio/library.js agents/dashboard/static/js/tc-studio/detail.js tests/unit/tc_library/test_tc_connectors_e2e.py
git commit -m "feat(tc-studio): W10 출처 변경 배너·재검토 필터·차이·확인 완료"
```

---

## Task W11: 문서 갱신 + 실제 계정 확인 + Phase 3 완료

**Files:**
- Modify: `doc/reference/API_REFERENCE.md`, `doc/guides/SCRIPTS_GUIDE.md`, `scripts/update_directory.py`, `doc/design/tc-studio/TC_AUTHORING_ELEMENT_SPEC.md`, `doc/development/tc-studio/TC_AUTHORING_ROADMAP.md`

- [ ] **Step 1: API 레퍼런스** — Phase 2에서 만든 "생성·검토" 표 아래에 C5 표를 그대로 옮기고, 한 줄을 붙인다: "원격 요청은 `_tc_fetch.fetch()`만 거친다: https·호스트 허용 목록·내부망 차단·리다이렉트 재검사(최대 3)·15초·20MB. 자격증명 파일 `config/confluence_config.json`, `config/figma_config.json`(git 제외), 환경변수 `CONFLUENCE_BASE_URL` `CONFLUENCE_EMAIL` `CONFLUENCE_TOKEN` `FIGMA_TOKEN`이 우선한다."

- [ ] **Step 2: 스크립트 가이드·디렉토리 설명** — `doc/guides/SCRIPTS_GUIDE.md`의 `_tc_generate.py` 행 아래:

```markdown
| `scripts/_tc_fetch.py` | 원격 문서 수집용 안전한 GET (SSRF 방어) | ❌ (다른 스크립트가 import) |
| `scripts/_tc_html.py` | HTML·Confluence storage → markdown | ❌ (다른 스크립트가 import) |
| `scripts/_tc_credentials.py` | Confluence·Figma 자격증명 (마스킹·환경변수 우선) | ❌ (대시보드가 import) |
| `scripts/_tc_connectors.py` | PRD URL·Confluence·Figma 소스 수집 | ❌ (대시보드가 import) |
| `scripts/_tc_source_watch.py` | 출처 버전 변경 확인·차이·확인 완료 | ❌ (대시보드가 import) |
```

`scripts/update_directory.py`의 `"_tc_generate.py"` 줄 아래:

```python
    "_tc_fetch.py":           "원격 문서 수집용 안전한 GET (SSRF 방어)",
    "_tc_html.py":            "HTML·Confluence storage → markdown",
    "_tc_credentials.py":     "Confluence·Figma 자격증명",
    "_tc_connectors.py":      "PRD URL·Confluence·Figma 소스 수집",
    "_tc_source_watch.py":    "출처 버전 변경 추적",
```

- [ ] **Step 3: 명세 정리** — `TC_AUTHORING_ELEMENT_SPEC.md` 8장의 `/api/authoring/credentials*` → `/api/tc-library/credentials*`, `/api/authoring/sources/diff` → `/api/tc-library/source-diff`, `/api/tc-library/{suite}/source-changes`에 `POST …/scan`을 추가하고 `/api/tc-library/cases/{case_id}/ack-source` → `/api/tc-library/{suite}/cases/{case_id}/ack-source`.

Run: `grep -c "/api/authoring/" doc/design/tc-studio/TC_AUTHORING_ELEMENT_SPEC.md`
Expected: `0`

- [ ] **Step 4: 실제 계정으로 확인** (테스트는 녹화 응답만 썼다)
  1. 대시보드 → 새로 생성 → 연결 설정: 회사 Confluence base URL·이메일·API 토큰, Figma 개인 토큰 저장 → 두 태그가 "연결됨"
  2. 실제 Confluence 기획 페이지 URL(`/pages/{id}` 형식과 `/x/…` 짧은 링크 각각) 수집 → 소스 칩의 ref가 `conf:{id}@v{n}`, 글자 수가 0이 아님, 표가 깨지지 않았는지 `GET /api/tc-library/sources/{bundle}/excerpt`로 확인
  3. 실제 Figma 프레임 URL(`node-id` 포함) 수집 → 화면 문구 수가 0이 아님, 검토 화면에 프레임 이미지가 보임
  4. 두 소스로 초안 생성 → Figma 문구 bullets가 "확인", PRD 문구가 "추정"
  5. Confluence 페이지를 한 글자 고친 뒤 라이브러리에서 "출처 변경 확인" → 배너 → 차이 → 확인 완료
  6. 응답 형식이 녹화본과 다르면 `connector_fixtures.py`를 실제 응답 모양으로 고치고 테스트부터 다시 맞춘다

- [ ] **Step 5: 완료 표시 + 커밋** — 로드맵 상단 "상세 계획" 표의 Phase 3 행에 `✅ 완료 (YYYY-MM-DD)`

```bash
git add doc/reference/API_REFERENCE.md doc/guides/SCRIPTS_GUIDE.md scripts/update_directory.py doc/design/tc-studio/TC_AUTHORING_ELEMENT_SPEC.md doc/development/tc-studio/TC_AUTHORING_ROADMAP.md
git commit -m "docs(tc-studio): W11 Phase 3 원격 소스·출처 추적 문서 갱신"
```

---

## Self-Review 결과

- **PRD 대응:** F1.3(C3 Confluence: Cloud·DC·짧은 링크·제목 주소·하위 페이지 깊이 1 최대 20, W9) · F1.4(C3 Figma: 프레임·문구·컴포넌트 variant·이동·PNG 10장, W9) · 목업 PRD URL 탭(C3 `add_url`, W9) · F5.9(C4, C5, W10) · §7 자격증명(C2, W9 설정 창)·SSRF(C1)
- **남은 위험:** 실제 Confluence·Figma 응답으로는 검증하지 않았다(W11 Step 4). Confluence storage의 복잡한 매크로(Jira 이슈 표, 레이아웃 섹션)는 본문 텍스트만 남는다.
- **이름 일관성:** `flags.source_change`, `needs_review`(필터 이름), `add_fetched`, `ref_base`, `TcConnectorRoutesMixin`·`_tcc_*`, `TCS_NS.sourceWatch`
