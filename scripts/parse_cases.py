"""
테스트 케이스 파일 파서.

지원 형식:
  - *.md  : Markdown 구조화 형식 (# Title / ## Precondition / ## Steps / ## Expected)
  - *.json: JSON 배열 형식 (기존 호환)

반환값: normalize된 test_cases 리스트
"""
import json
import re
from pathlib import Path


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """
    YAML frontmatter(--- 블록)를 파싱해 메타데이터 dict와 본문을 반환.

    Returns:
        (metadata_dict, body_text)
    """
    if not text.startswith("---"):
        return {}, text

    end = text.find("---", 3)
    if end == -1:
        return {}, text

    fm_block = text[3:end].strip()
    body = text[end + 3:].strip()

    meta = {}
    for line in fm_block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        # 배열 파싱: [a, b, c]
        if val.startswith("[") and val.endswith("]"):
            meta[key] = [v.strip() for v in val[1:-1].split(",")]
        elif val.lower() == "null":
            meta[key] = None
        else:
            meta[key] = val
    return meta, body


def parse_md(text: str) -> list:
    """
    Markdown 파일을 test_cases 리스트로 파싱.

    형식:
        # 케이스 타이틀

        ## Precondition
        0. 사전 조건 내용

        ## Steps
        1. 첫 번째 스텝
        2. 두 번째 스텝

        ## Expected
        - 기대 결과

        ---   (케이스 구분자)
    """
    # frontmatter 추출
    meta, body = _parse_frontmatter(text)

    cases = []
    blocks = re.split(r"^\s*---+\s*$", body, flags=re.MULTILINE)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        title_match = re.search(r"^#\s+(.+)$", block, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else meta.get("title", "unnamed")

        precondition = _extract_section(block, "Precondition", "전제 조건", "사전 조건")
        steps_raw = _extract_section(block, "Steps", "테스트 절차", "절차", "단계")
        expected = _extract_section(block, "Expected", "기대 결과", "예상 결과")

        # Steps: 번호 있는 줄들을 리스트로
        steps = [
            line.strip()
            for line in steps_raw.splitlines()
            if re.match(r"^\d+\.", line.strip())
        ] if steps_raw else []

        case = {
            "title": title,
            "precondition": precondition.strip(),
            "steps": steps,
            "expected": expected.strip(),
            "format": meta.get("type", "structured"),
        }
        # frontmatter 메타데이터 포함
        if meta:
            case["id"] = meta.get("id")
            case["data_key"] = meta.get("data_key")
            case["priority"] = meta.get("priority")
            case["tags"] = meta.get("tags", [])

        cases.append(case)

    return cases


def _extract_section(text: str, *section_aliases: str) -> str:
    """## Section 헤더 아래의 내용을 추출. 영문·한글 alias 모두 시도."""
    for section in section_aliases:
        pattern = rf"##\s+{re.escape(section)}\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def parse_json(text: str) -> list:
    """JSON 배열을 test_cases 리스트로 파싱 (기존 형식 호환)."""
    raw = json.loads(text)
    normalized = []
    for item in raw:
        if isinstance(item, str):
            normalized.append({
                "title": item,
                "precondition": "",
                "steps": [],
                "expected": "",
                "format": "natural",
            })
        elif isinstance(item, dict):
            normalized.append({
                "title": item.get("title", "unnamed"),
                "precondition": item.get("precondition", ""),
                "steps": item.get("steps", []),
                "expected": item.get("expected", ""),
                "format": "structured",
            })
    return normalized


def validate_data_keys(cases: list, group: str, test_data_path: str | Path = None) -> list:
    """
    케이스들의 data_key가 test_data.json에 존재하는지 검증.
    Returns: 누락된 data_key 리스트
    """
    if test_data_path is None:
        test_data_path = Path(__file__).resolve().parent.parent / "config" / "test_data.json"

    test_data_path = Path(test_data_path)
    if not test_data_path.exists():
        return []

    with open(test_data_path, encoding="utf-8") as f:
        all_data = json.load(f)

    group_data = all_data.get(group, {})
    missing = []

    for case in cases:
        dk = case.get("data_key")
        if dk is None:
            continue
        if dk not in group_data:
            missing.append(dk)

    if missing:
        print(f"[경고] test_data.json에 누락된 data_key ({group}): {', '.join(missing)}")

    return missing


def _natural_sort_key(p: Path) -> list:
    """파일명을 숫자 기준으로 정렬하는 키 (tc_10 > tc_9 보장)."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", p.name)]


def load_cases(path: str | Path) -> list:
    """
    파일 또는 디렉토리 경로에 따라 자동으로 파서를 선택해 test_cases를 반환.
    디렉토리일 경우 내부의 모든 .md, .json 파일을 파싱해 합산함.

    Args:
        path: .md/.json 파일 경로 또는 디렉토리 경로

    Returns:
        normalize된 test_cases 리스트
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"케이스 파일 혹은 디렉토리 없음: {p}")

    if p.is_dir():
        all_cases = []
        # tc_*.md / tc_*.json 파일만 (targets.json 등 비케이스 파일 제외), 자연 정렬
        files = sorted(
            list(p.glob("tc_*.md")) + list(p.glob("tc_*.json")),
            key=_natural_sort_key,
        )
        for f in files:
            all_cases.extend(load_cases(f))
        return all_cases

    text = p.read_text(encoding="utf-8")

    if p.suffix == ".md":
        return parse_md(text)
    elif p.suffix == ".json":
        return parse_json(text)
    else:
        raise ValueError(f"지원하지 않는 형식: {p.suffix}  (.md 또는 .json만 지원)")
