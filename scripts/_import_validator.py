"""Import 유효성 검사 및 분류 모듈 (Import Studio S2 BE)"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

REQUIRED_FIELDS = ["tc_id", "title", "steps", "expected"]
TC_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


def compute_hash(row: dict) -> str:
    """title + precondition + steps + expected 내용 SHA256 앞 8자리."""
    content = (
        f"{row.get('title', '')}|{row.get('precondition', '') or ''}"
        f"|{row.get('steps', '')}|{row.get('expected', '')}"
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]


def _parse_testcase_md(path: Path) -> dict:
    """Read the testcase fields needed for comparison without executing YAML.

    Import Studio emits JSON-compatible YAML scalars, while older testcase
    files may use a simple ``[tag, tag]`` flow list.  Supporting only those
    scalar shapes keeps this reader deterministic and safe.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}

    frontmatter = ""
    fm_match = re.match(r"^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|\Z)", text)
    if fm_match:
        frontmatter = fm_match.group(1)

    def _frontmatter_value(name: str) -> str:
        match = re.search(rf"^{re.escape(name)}:\s*(.*)$", frontmatter, re.MULTILINE)
        return match.group(1).strip() if match else ""

    priority_raw = _frontmatter_value("priority")
    try:
        priority = json.loads(priority_raw) if priority_raw else ""
    except json.JSONDecodeError:
        priority = priority_raw.strip("'\"")

    tags_raw = _frontmatter_value("tags")
    tags: list[str] = []
    if tags_raw:
        try:
            parsed_tags = json.loads(tags_raw)
            if isinstance(parsed_tags, list):
                tags = [str(tag) for tag in parsed_tags]
        except json.JSONDecodeError:
            if tags_raw.startswith("[") and tags_raw.endswith("]"):
                tags = [tag.strip().strip("'\"") for tag in tags_raw[1:-1].split(",") if tag.strip()]

    # 제목: frontmatter 이후 첫 번째 # 헤딩
    title = ""
    title_m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if title_m:
        title = title_m.group(1).strip()

    # 사전 조건 섹션
    precondition = ""
    pre_m = re.search(r"##\s+사전\s*조건\n([\s\S]*?)(?=\n##\s|\Z)", text)
    if pre_m:
        precondition = pre_m.group(1).strip()

    # Steps 섹션
    steps = ""
    steps_m = re.search(r"##\s+Steps\n([\s\S]*?)(?=\n##\s|\Z)", text)
    if steps_m:
        steps = steps_m.group(1).strip()

    # Expected 섹션
    expected = ""
    expected_m = re.search(r"##\s+Expected\n([\s\S]*?)(?=\n##\s|\Z)", text)
    if expected_m:
        expected = expected_m.group(1).strip()

    return {
        "title": title,
        "precondition": precondition,
        "steps": steps,
        "expected": expected,
        "priority": str(priority),
        "tags": tags,
    }


def _extract_hash_from_md(path: Path) -> str:
    fields = _parse_testcase_md(path)
    if not fields:
        return ""
    return compute_hash(fields)


def load_existing_testcases(testcases_dir: Path) -> dict:
    """testcases/ 하위 모든 tc_*.md 파일 스캔.

    Returns:
        {
            tc_id: {
                "group": "folder_name",
                "hash": "abc12345",
                "path": Path,
            }
        }

    tc_id는 파일명 prefix(tc_01) 또는 YAML frontmatter의 id 필드로 판단한다.
    frontmatter 파싱 없이 실용적으로: 파일명 stem(tc_01_login_success)에서
    숫자 prefix(tc_01)를 추출하고, 제목 기반 해시를 계산한다.

    만약 frontmatter에 `id:` 필드가 있으면 그것을 tc_id로 사용한다.
    """
    existing: dict = {}

    if not testcases_dir.exists():
        return existing

    for group_dir in testcases_dir.iterdir():
        if not group_dir.is_dir() or group_dir.name.startswith("."):
            continue
        for md_file in group_dir.glob("tc_*.md"):
            tc_id = _extract_tc_id(md_file)
            if not tc_id:
                continue
            fields = _parse_testcase_md(md_file)
            file_hash = compute_hash(fields) if fields else ""
            existing[tc_id] = {
                "group": group_dir.name,
                "hash": file_hash,
                "path": md_file,
                **fields,
            }

    return existing


def _extract_tc_id(md_file: Path) -> str:
    """md 파일에서 tc_id를 추출.

    우선순위:
    1. YAML frontmatter의 `id:` 필드 값
    2. 파일명의 숫자 prefix (tc_01 형식)
    """
    try:
        text = md_file.read_text(encoding="utf-8")
    except OSError:
        return ""

    # frontmatter id: 필드 시도
    fm_m = re.match(r"^---\n([\s\S]*?)\n---", text)
    if fm_m:
        id_m = re.search(r"^id:\s*(.+)$", fm_m.group(1), re.MULTILINE)
        if id_m:
            val = id_m.group(1).strip()
            try:
                decoded = json.loads(val)
                if isinstance(decoded, str):
                    val = decoded
            except json.JSONDecodeError:
                val = val.strip("'\"")
            # "null" 또는 빈값은 파일명 fallback
            if val and val.lower() != "null":
                return val

    # 파일명에서 tc_숫자 prefix 추출 (tc_01_login_success.md → tc_01)
    stem_m = re.match(r"(tc_\d+)", md_file.stem)
    if stem_m:
        return stem_m.group(1)

    return ""


def classify_row(row: dict, existing: dict) -> dict:
    """행 분류.

    Args:
        row: parse_sheet()가 반환한 행 dict
        existing: load_existing_testcases()가 반환한 {tc_id: {...}} 매핑

    Returns:
        {"status": "added|updated|conflict|error|same", "reason": "..."}
    """
    # 필수 필드 검사
    for f in REQUIRED_FIELDS:
        if not str(row.get(f, "")).strip():
            return {"status": "error", "reason": f"필수 필드 누락: {f}",
                    "reason_code": f"MISSING_{f.upper()}"}

    tc_id = row["tc_id"].strip()
    row_group = row.get("group", "").strip()

    if not TC_ID_PATTERN.fullmatch(tc_id):
        return {"status": "error", "reason": "tc_id 형식 오류", "reason_code": "INVALID_TC_ID"}
    if not row_group or not re.fullmatch(r"[A-Za-z0-9가-힣_-]+", row_group):
        return {"status": "error", "reason": "group 형식 오류", "reason_code": "INVALID_GROUP"}

    if tc_id not in existing:
        return {"status": "added", "reason": "신규 tc_id", "reason_code": "NEW_TC_ID"}

    existing_entry = existing[tc_id]

    # conflict: 같은 tc_id가 다른 그룹에 존재
    if row_group and existing_entry["group"] != row_group:
        return {
            "status": "conflict",
            "reason": (
                f"tc_id {tc_id}가 {existing_entry['group']} 그룹에 이미 존재"
            ),
            "reason_code": "GROUP_CONFLICT",
        }

    # 해시 비교
    current_hash = compute_hash(row)
    if current_hash == existing_entry["hash"]:
        return {"status": "same", "reason": "변경 없음", "reason_code": "UNCHANGED"}

    return {"status": "updated", "reason": f"내용 변경 (hash: {current_hash})",
            "reason_code": "CONTENT_CHANGED"}
