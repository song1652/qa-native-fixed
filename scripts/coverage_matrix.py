"""
커버리지 매트릭스 생성기
testcases/ 각 그룹 폴더의 tc_*.md를 파싱하여 태그·우선순위 분포를 집계하고
state/coverage.json에 저장한다.
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
TESTCASES_DIR = PROJECT_ROOT / "testcases"
PAGES_JSON = PROJECT_ROOT / "config" / "pages.json"
COVERAGE_PATH = PROJECT_ROOT / "state" / "coverage.json"

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


def build_coverage() -> dict:
    from parse_cases import load_cases

    pages = {}
    if PAGES_JSON.exists():
        try:
            pages = json.loads(PAGES_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass

    result = {}
    covered_groups = set()

    if TESTCASES_DIR.exists():
        for group_dir in sorted(TESTCASES_DIR.iterdir()):
            if not group_dir.is_dir():
                continue
            group = group_dir.name
            try:
                cases = load_cases(str(group_dir))
            except Exception:
                cases = []
            if not cases:
                continue

            covered_groups.add(group)
            tags_count: dict[str, int] = {}
            priority_count: dict[str, int] = {"very_high": 0, "high": 0, "medium": 0, "low": 0}

            for c in cases:
                for tag in c.get("tags", []):
                    t = tag.strip().lower()
                    if t:
                        tags_count[t] = tags_count.get(t, 0) + 1
                pri = c.get("priority", "low")
                if pri in priority_count:
                    priority_count[pri] += 1
                else:
                    priority_count["low"] += 1

            # 태그 Top 8만 유지
            top_tags = dict(
                sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:8]
            )

            result[group] = {
                "total": len(cases),
                "tags": top_tags,
                "priority": priority_count,
                "url": pages.get(group, {}).get("url", "") if isinstance(pages.get(group), dict) else "",
            }

    # pages.json에 있지만 testcases/ 폴더 없는 그룹 = 미커버
    uncovered = [
        g for g in pages
        if g not in covered_groups and not (TESTCASES_DIR / g).is_dir()
    ]
    result["_uncovered"] = uncovered

    return result


def main():
    data = build_coverage()
    COVERAGE_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    total_cases = sum(v["total"] for k, v in data.items() if not k.startswith("_"))
    groups = [k for k in data if not k.startswith("_")]
    print(f"[coverage_matrix] {len(groups)}개 그룹, 총 {total_cases}건 집계 → {COVERAGE_PATH}")
    for g in groups:
        print(f"  {g}: {data[g]['total']}건  태그={list(data[g]['tags'].keys())[:4]}")
    if data.get("_uncovered"):
        print(f"  미커버 그룹: {data['_uncovered']}")


if __name__ == "__main__":
    main()
