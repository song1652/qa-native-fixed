---
id: "IMPSET_01"
data_key: null
priority: "high"
tags: ["validation", "content"]
type: structured
source_ref: "tc-library:TC스튜디오_가져오기통합/S01_0002"
---
# 이메일 형식 오류 시 안내 문구 표시

## 사전 조건
새 페이지에서 시작한다.

## Steps
1. http://localhost:8877 에 접속한다.
2. 이름에 "테스터"를 입력한다.
3. 이메일에 "invalid"를 입력한다.
4. 등록 버튼을 누른다.

## Expected
이메일 형식 오류 안내가 표시된다.
- "이메일 형식을 확인하세요."
