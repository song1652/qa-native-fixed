"""브라우저 가이드의 목차·다른 가이드·이미지가 실제 파일로 연결되는지 확인."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[3]
GUIDES = [ROOT / 'doc/guides/USER_GUIDE.html',
          ROOT / 'doc/guides/tc-studio/TC_AUTHORING_USER_GUIDE.html',
          ROOT / 'doc/guides/SCRIPTS_GUIDE.html', ROOT / 'doc/guides/TEST_CASE_GUIDE.html']


class PageLinks(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = []
        self.links = []
        self.images = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if tag == 'img':
            self.images.append(attrs)
            self.links.append(attrs['src'])


def test_html_guides_have_valid_navigation_and_images():
    for path in GUIDES:
        assert path.exists(), f'HTML 가이드 없음: {path}'
        page = PageLinks(path.read_text())
        assert len(page.ids) == len(set(page.ids)), f'중복 목차 ID: {path}'
        for image in page.images:
            assert image.get('alt'), f'이미지 설명 누락: {path}: {image}'
        for href in page.links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            target = path.parent / unquote(url.path) if url.path else path
            assert target.exists(), f'끊어진 링크: {path}: {href}'
            if url.fragment and target.suffix == '.html':
                ids = PageLinks(target.read_text()).ids
                assert unquote(url.fragment) in ids, f'없는 목차: {path}: {href}'
