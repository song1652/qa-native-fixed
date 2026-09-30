"""
test_data/ 동기화 스크립트.
testcases/ 폴더의 tc_*.md frontmatter에서 data_key를 추출하고,
test_data/{product}.json에 누락된 키가 있으면 빈 템플릿을 자동 추가한다.

사용법: python scripts/sync_test_data.py [--dry-run]

구조:
  test_data/serveone.json   → data_key "serveone" 매핑
  test_data/saucedemo.json  → data_key "saucedemo" 매핑
"""
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
from parse_cases import load_cases, split_data_key
from _paths import TEST_DATA_DIR, load_test_data


def main():
    project_root = Path(__file__).resolve().parent.parent
    if not TEST_DATA_DIR.exists():
        print(f"[오류] test_data/ 폴더가 없습니다: {TEST_DATA_DIR}")
        sys.exit(1)
    sync(project_root / "testcases", dry_run="--dry-run" in sys.argv)


def sync(testcases_dir: Path, *, dry_run: bool = False) -> int:
    """케이스의 data_key가 가리키는 test_data/{프로덕트}.json[데이터셋]이 없으면 빈 칸을 만든다. 추가한 개수를 돌려준다."""

    # 현재 전체 test_data 로드 (product → data_key dict)
    test_data = load_test_data()

    added_count = 0

    for group_dir in sorted(testcases_dir.iterdir()):
        if not group_dir.is_dir() or group_dir.name.startswith("."):
            continue

        group = group_dir.name
        cases = load_cases(group_dir)

        for case in cases:
            dk = case.get("data_key")
            if dk is None:
                continue
            # test_data[프로덕트][데이터셋] (parse_cases.split_data_key, PRD O1)
            product, dataset = split_data_key(dk, group)
            product_file = TEST_DATA_DIR / f"{product}.json"
            product_example = TEST_DATA_DIR / f"{product}.example.json"
            product_data = test_data.get(product, {})
            if dataset in product_data:
                continue
            product_data[dataset] = {}
            added_count += 1
            print(f"  [추가] test_data/{product}.json → [{dataset}]  (케이스 그룹: {group})")
            if not dry_run:
                current = (json.loads(product_file.read_text(encoding="utf-8")) if product_file.exists()
                           else {"_comment": f"{product} 테스트 데이터. 이 파일은 gitignored입니다."})
                current[dataset] = {}
                product_file.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                if not product_example.exists():
                    example = {"_comment": f"{product} 테스트 데이터 템플릿. cp {product}.example.json {product}.json 후 값 입력.",
                               dataset: {}}
                    product_example.write_text(json.dumps(example, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            test_data[product] = product_data

    if added_count == 0:
        print("[동기화] 누락된 data_key 없음. test_data/ 폴더가 최신입니다.")
        return 0

    if dry_run:
        print(f"\n[dry-run] {added_count}개 키 추가 예정 (실제 저장하지 않음)")
    else:
        print(f"\n[완료] {added_count}개 키 추가됨 → {TEST_DATA_DIR}")
    return added_count


if __name__ == "__main__":
    main()
