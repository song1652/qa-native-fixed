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
from parse_cases import load_cases
from _paths import TEST_DATA_DIR, load_test_data


def main():
    dry_run = "--dry-run" in sys.argv

    project_root = Path(__file__).resolve().parent.parent
    testcases_dir = project_root / "testcases"

    if not TEST_DATA_DIR.exists():
        print(f"[오류] test_data/ 폴더가 없습니다: {TEST_DATA_DIR}")
        sys.exit(1)

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

            # dk에 해당하는 product 파일이 없으면 생성
            product_file = TEST_DATA_DIR / f"{dk}.json"
            product_example = TEST_DATA_DIR / f"{dk}.example.json"

            # 현재 product 데이터 로드
            product_data = test_data.get(dk, {})

            # group 키가 없으면 추가
            if group not in product_data:
                product_data[group] = {"username": "", "password": ""}
                added_count += 1
                print(f"  [추가] test_data/{dk}.json → [{group}]")

                if not dry_run:
                    # 실제 파일에 저장
                    if product_file.exists():
                        with open(product_file, encoding="utf-8") as f:
                            current = json.load(f)
                    else:
                        current = {
                            "_comment": f"{dk} 테스트 데이터. 이 파일은 gitignored입니다."
                        }
                    current[group] = product_data[group]
                    with open(product_file, "w", encoding="utf-8") as f:
                        json.dump(current, f, ensure_ascii=False, indent=2)
                        f.write("\n")

                    # example 파일도 없으면 같이 생성
                    if not product_example.exists():
                        example = {
                            "_comment": f"{dk} 테스트 데이터 템플릿. cp {dk}.example.json {dk}.json 후 값 입력."
                        }
                        example[group] = {"username": "", "password": ""}
                        with open(product_example, "w", encoding="utf-8") as f:
                            json.dump(example, f, ensure_ascii=False, indent=2)
                            f.write("\n")

                # 캐시 갱신
                test_data[dk] = product_data

    if added_count == 0:
        print("[동기화] 누락된 data_key 없음. test_data/ 폴더가 최신입니다.")
        return

    if dry_run:
        print(f"\n[dry-run] {added_count}개 키 추가 예정 (실제 저장하지 않음)")
    else:
        print(f"\n[완료] {added_count}개 키 추가됨 → {TEST_DATA_DIR}")


if __name__ == "__main__":
    main()
