# test_data/ — 프로덕트별 테스트 데이터

각 프로덕트의 테스트 입력값(URL, 자격증명, 입력 폼 데이터 등)을 **파일 단위로 분리**해 관리합니다.

## 구조

```
test_data/
  {product}.json          ← 실제 데이터 (gitignored, 로컬 전용)
  {product}.example.json  ← 빈 템플릿 (git 추적, 팀 공유용)
  README.md
```

## 새 프로젝트 셋업

```bash
# 사용할 프로덕트 템플릿을 복사해서 실제 데이터로 채우세요
cp test_data/serveone.example.json test_data/serveone.json
```

## 프로덕트 추가

1. `test_data/{product}.example.json` 생성 (빈 구조, git 커밋)
2. `test_data/{product}.json` 생성 (실제 값 입력, gitignore됨)
3. `config/pages.json`에 해당 그룹 URL 매핑 추가

## 로딩 방식

`scripts/_paths.py`의 `load_test_data()` 함수가 `*.json` 파일을 자동으로 머지합니다.
파일명(stem)이 곧 `test_data[key]`가 됩니다.

```python
# 예: test_data/serveone.json → load_test_data()["serveone"]
from _paths import load_test_data
data = load_test_data()
serveone_creds = data["serveone"]["login"]
```

## 현재 프로덕트

| 파일 | 설명 |
|------|------|
| `serveone.json` | ServeOne B2B 쇼핑몰 (고객/협력사 로그인 등) |
| `saucedemo.json` | Saucedemo (데모 e-commerce 사이트) |
