"""목업 <style>을 대시보드용 .tc-studio 스코프 CSS로 옮긴다 (계획 W1에서 한 번 실행 후 결과를 커밋).

사용: .venv/bin/python scope_css.py design-previews/tc-authoring-studio.html agents/dashboard/static/css/tc-studio.css
규칙:
- 다크 전용 대시보드이므로 라이트 테마 블록(@media prefers-color-scheme, [data-theme=...])은 버린다.
- `:root { … }` 토큰은 `.tc-studio { … }`로 옮긴다 (Import Studio의 .import-studio 방식과 같다).
- `body { … }` 규칙은 `.tc-studio { … }`로 바꾼다.
- 나머지 모든 선택자 앞에 `.tc-studio `를 붙인다. @media 안쪽도 같다. @keyframes는 그대로 둔다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# 목업 CSS를 대시보드에 붙일 때 필요한 보정. 목업의 .chip-select.empty는 빈 화면용 .empty
# (padding 60px, display:grid)와 이름이 겹쳐 행 높이가 커지므로 클래스를 is-unset으로 바꿔 쓴다.
EXTRA = """
/* ── 대시보드 보정 (scope_css.py EXTRA) ── */
.tc-studio { padding:16px; }
.tc-studio .chip-select.is-unset { color:var(--text3); font-style:italic; }
.tc-studio .chip-select.result-none { color:var(--text3); }
"""
HEADER = "/* TC 스튜디오 — design-previews/tc-authoring-studio.html <style>에서 생성 (scope_css.py). 직접 고치지 말고 목업을 고친 뒤 다시 생성한다. */\n"


def _blocks(css: str):
    """최상위 블록을 (prelude, body) 로 나눈다. 중괄호 깊이만 센다."""
    i, n = 0, len(css)
    while i < n:
        start = css.find("{", i)
        if start == -1:
            return
        prelude = css[i:start].strip()
        depth, j = 1, start + 1
        while depth and j < n:
            depth += {"{": 1, "}": -1}.get(css[j], 0)
            j += 1
        yield prelude, css[start + 1:j - 1]
        i = j


def _scope_selectors(prelude: str) -> str:
    parts = []
    for sel in prelude.split(","):
        sel = sel.strip()
        if sel in ("body", ":root"):
            parts.append(".tc-studio")
        elif sel.startswith("*"):
            parts.append(f".tc-studio {sel}")
        else:
            parts.append(f".tc-studio {sel}")
    return ", ".join(dict.fromkeys(parts))


def scope(css: str) -> str:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out = [HEADER]
    for prelude, body in _blocks(css):
        if prelude.startswith("@media") and "prefers-color-scheme" in prelude:
            continue
        if "data-theme" in prelude:
            continue
        if prelude.startswith("@keyframes"):
            out.append(f"{prelude} {{{body}}}\n")
        elif prelude.startswith("@media"):
            inner = "".join(f"  {_scope_selectors(p)} {{{b}}}\n" for p, b in _blocks(body))
            out.append(f"{prelude} {{\n{inner}}}\n")
        else:
            out.append(f"{_scope_selectors(prelude)} {{{body}}}\n")
    return "".join(out) + EXTRA


def main(src: str, dst: str) -> None:
    html = Path(src).read_text(encoding="utf-8")
    css = re.search(r"<style>(.*?)</style>", html, re.S).group(1)
    Path(dst).write_text(scope(css), encoding="utf-8")


if __name__ == "__main__":
    main(*sys.argv[1:3])
