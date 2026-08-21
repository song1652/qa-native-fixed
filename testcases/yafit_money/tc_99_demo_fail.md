---
id: tc_99
data_key: null
priority: low
tags: [demo, negative]
type: structured
---
<!-- 이 TC는 정규 실행에서 skip 처리됨 (tests/generated/.../tc_99_demo_fail.py 참고) -->
# 의도적 실패 데모 — 아티팩트 렌더링 확인

## Precondition
0. https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html 접속

## Steps
1. 페이지 로드 완료 대기 (domcontentloaded)
2. 1.5초 대기
3. 헤딩(h1/h2/h3) 요소가 화면에 표시되는지 확인
4. 존재하지 않는 요소(#this-element-does-not-exist-for-demo) 표시 여부 확인

## Expected
- 헤딩 요소가 화면에 표시되어야 한다.
- #this-element-does-not-exist-for-demo 요소가 화면에 표시되어야 한다. (의도적 실패)
