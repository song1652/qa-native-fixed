"""새로 클론한 저장소의 실행 환경 준비 — README '설치'의 Python 패키지·테스트 데이터 단계를 한 번에 실행.

    python3 scripts/setup_env.py

여러 번 실행해도 안전하다. 이미 있는 test_data/{프로덕트}.json은 덮어쓰지 않는다.
"""
from __future__ import annotations

import shutil
import subprocess
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = ROOT / ".venv" / "bin" / "python3"  # .claude/settings.json 훅이 이 경로를 쓴다


def copy_test_data(test_data_dir: Path) -> list[Path]:
    """*.example.json 템플릿 중 실제 파일이 없는 것만 복사하고, 만든 파일 목록을 반환."""
    created = []
    for example in sorted(test_data_dir.glob("*.example.json")):
        target = example.with_name(example.name.removesuffix(".example.json") + ".json")
        if not target.exists():
            shutil.copyfile(example, target)
            created.append(target)
    return created


def main() -> None:
    if not VENV_PYTHON.exists():
        venv.create(ROOT / ".venv", with_pip=True)
    subprocess.run([str(VENV_PYTHON), "-m", "pip", "install", "-q", "-r", str(ROOT / "requirements.txt")], check=True)
    subprocess.run([str(VENV_PYTHON), "-m", "playwright", "install", "chromium"], check=True)
    for path in copy_test_data(ROOT / "test_data"):
        print(f"테스트 데이터 템플릿 복사: {path.relative_to(ROOT)}")
    print("완료: .venv · Python 패키지 · Chromium · test_data")


if __name__ == "__main__":
    main()
