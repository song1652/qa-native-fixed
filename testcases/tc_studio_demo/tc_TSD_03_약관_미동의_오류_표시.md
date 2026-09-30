---
id: "TSD_03"
data_key: null
priority: "high"
tags: ["negative", "content"]
type: structured
source_ref: "tc-library:TC스튜디오_실사용/TC_0003"
---
# 약관 미동의 오류 표시

## 사전 조건
새 페이지에서 시작한다.

## Steps
1. 이름에 "테스터"를 입력한다
2. 이메일에 "qa@example.test"를 입력한다
3. 약관 동의를 체크하지 않은 상태로 둔다
4. 등록 버튼을 누른다

## Expected
약관 동의를 요구하는 오류 메시지가 표시된다.
- "약관에 동의하세요."
