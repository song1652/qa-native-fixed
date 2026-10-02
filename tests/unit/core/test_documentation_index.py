"""문서 재분류 후 자동 생성기가 현재 문서를 빠뜨리지 않는지 확인한다."""
from pathlib import Path

from scripts import update_directory


def test_directory_generator_lists_current_documents():
    root = Path(__file__).resolve().parents[3]
    assert update_directory.DOC_PATH == root / 'doc/reference/DIRECTORY.md'
    generated = update_directory.build_markdown()
    for document in (root / 'doc').rglob('*'):
        if document.suffix not in {'.md', '.html'}:
            continue
        assert document.relative_to(root / 'doc').as_posix() in generated
