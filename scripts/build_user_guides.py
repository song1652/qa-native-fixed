"""Markdown 원본으로 HTML 가이드를 갱신한다. --check는 미갱신 파일을 검출한다.

설치: python3 -m pip install -r requirements-docs.txt
실행: python3 scripts/build_user_guides.py [--check]
"""
from __future__ import annotations

import argparse
import html
import os
from pathlib import Path
import re

import markdown
from markdown.extensions.toc import slugify_unicode

ROOT = Path(__file__).resolve().parents[1]
GUIDES = {
    ROOT / 'doc/guides/DASHBOARD_USER_GUIDE.md': ROOT / 'doc/guides/USER_GUIDE.html',
    ROOT / 'doc/guides/tc-studio/TC_AUTHORING_USER_GUIDE.md': ROOT / 'doc/guides/tc-studio/TC_AUTHORING_USER_GUIDE.html',
    ROOT / 'doc/guides/SCRIPTS_GUIDE.md': ROOT / 'doc/guides/SCRIPTS_GUIDE.html',
    ROOT / 'doc/guides/TEST_CASE_GUIDE.md': ROOT / 'doc/guides/TEST_CASE_GUIDE.html',
}


def render(source: Path, target: Path) -> str:
    text = source.read_text(encoding='utf-8')
    # 기존 TC 가이드의 명시적 링크를 헤더 ID로 옮겨 중복 ID를 방지한다.
    text = re.sub(r'<a id="([^"]+)"></a>\s*\n## ([^\n]+)', r'## \2 {#\1}', text)
    # HTML의 목차는 실제 헤더에서 생성하므로 본문의 중복 목차는 제거한다.
    text = re.sub(r'## 목차\n.*?(?=\n## 1\.)', '', text, flags=re.S)
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'sane_lists', 'attr_list', 'toc'],
                           extension_configs={'toc': {'slugify': slugify_unicode, 'toc_depth': '2-2'}})
    body = md.convert(text)

    def link(match):
        href = html.unescape(match[1])
        path, sep, fragment = href.partition('#')
        mapped = GUIDES.get((source.parent / path).resolve()) if path else None
        if mapped:
            href = os.path.relpath(mapped, target.parent) + sep + fragment
        return 'href="' + html.escape(href, quote=True) + '"'

    body = re.sub(r'href="([^"]*)"', link, body)
    body = body.replace('<table>', '<div class="table-wrap"><table>').replace('</table>', '</table></div>')
    body = re.sub(r'<p>(<img[^>]+>)</p>', lambda m: '<figure class="shot"><a href="' +
                  re.search(r'src="([^"]+)"', m[1])[1] + '" target="_blank" rel="noopener">' +
                  m[1].replace('<img ', '<img loading="lazy" ') + '</a></figure>', body)
    title = html.escape(text.splitlines()[0].lstrip('# '))
    css = os.path.relpath(ROOT / 'doc/guides/guide.css', target.parent)
    guide_links = '\n'.join(f'<a href="{os.path.relpath(dst, target.parent)}">{label}</a>'
                            for dst, label in zip(GUIDES.values(), ['대시보드', 'TC 스튜디오', '스크립트', 'TC 작성']))
    return f'''<!DOCTYPE html>
<!-- 자동 생성: scripts/build_user_guides.py. 수정 원본: {source.relative_to(ROOT)} -->
<html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light"><title>{title}</title>
<link rel="stylesheet" href="{css}">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
</head><body><a class="skip-link" href="#content">본문으로 이동</a>
<header class="topbar"><div class="brand">QA 컨트롤 센터</div><span>사용 가이드</span><span class="updated">최신 밝은 테마</span></header>
<div class="layout"><nav class="sidebar" aria-label="가이드 목차"><div class="nav-label">사용 가이드</div>{guide_links}<div class="nav-label">이 문서의 목차</div>{md.toc}</nav>
<main class="main" id="content"><details class="mobile-toc"><summary>목차 열기</summary>{guide_links}{md.toc}</details>
{body}
<footer>QA 컨트롤 센터 · 웹 QA · <a href="http://localhost:8766/">대시보드 열기</a><br>이미지는 누르면 원본 크기로 볼 수 있습니다. 인쇄는 브라우저의 인쇄 기능을 사용하세요.</footer>
</main></div>
<script>
const links=document.querySelectorAll('.sidebar .toc a');
const observer=new IntersectionObserver(entries=>{{entries.forEach(entry=>{{if(entry.isIntersecting){{
links.forEach(link=>{{if(link.hash==='#'+entry.target.id)link.setAttribute('aria-current','true');else link.removeAttribute('aria-current');}});
}}}});}},{{rootMargin:'-15% 0px -70% 0px'}});
document.querySelectorAll('main>h2').forEach(heading=>observer.observe(heading));
</script></body></html>
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='원본과 HTML의 불일치만 확인')
    args = parser.parse_args()
    stale = []
    for source, target in GUIDES.items():
        content = render(source, target)
        if args.check:
            if not target.exists() or target.read_text(encoding='utf-8') != content:
                stale.append(str(target.relative_to(ROOT)))
        else:
            target.write_text(content, encoding='utf-8')
            print(target.relative_to(ROOT))
    if stale:
        print('HTML 갱신 필요: ' + ', '.join(stale))
    return bool(stale)


if __name__ == '__main__':
    raise SystemExit(main())
