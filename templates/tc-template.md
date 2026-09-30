---
id: "{그룹코드}_{번호}"
data_key: {프로덕트}.{데이터셋} | null
priority: very_high | high | medium | low
tags: [{유형}, {분류}]
type: structured | natural
---
# {테스트 제목 — 15자 이내, 무엇을 검증하는지 한눈에}

## Precondition
0. {테스트 시작 전 시스템 상태}

## Steps
1. {필드명} 필드에 test_data[{프로덕트}][{데이터셋}].{속성} 입력
2. {필드명} 필드에 test_data[{프로덕트}][{데이터셋}].{속성} 입력
3. {버튼명} 버튼 클릭

## Expected
- {구체적 텍스트/상태/UI 요소 — "정상 동작" 금지}
- {추가 검증 포인트}

<!--
작성 규칙 요약:
- 파일명: tc_{그룹코드}_{번호}_{설명}.md (예: tc_CL_01_로그인_성공.md) 또는 tc_{번호}_{설명}.md
- id: "{그룹코드}_{번호}" 형식으로 따옴표 포함 작성 (예: "CL_01", "PL_02") — 따옴표 없으면 파서가 정상 매핑 못할 수 있음
- 1파일 = 1케이스
- frontmatter 필수: id, data_key, priority, tags, type
- data_key: "{프로덕트}.{데이터셋}" 형식. test_data/{프로덕트}.json 안의 {데이터셋} 키를 가리킴 (예: serveone.login). 점이 없으면 그룹 폴더명을 프로덕트로 봄. 입력값 불필요 시 null
- Steps의 입력값은 test_data[프로덕트][데이터셋] 참조 (하드코딩 금지)
- Steps: 번호(1. 2. 3.) 형식 권장; 번호 없는 평문 줄도 파서 지원
- UI 텍스트는 영어 원문 그대로 (번역 금지)
- 유형 태그: positive, negative, smoke, auth, validation, security, edge_case, session, navigation, content
- 우선순위: very_high(차단급 핵심 흐름) high(핵심기능) medium(보조기능) low(엣지케이스)
-->
