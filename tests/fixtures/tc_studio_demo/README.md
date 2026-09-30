# TC Studio 실사용 검증 페이지

사용자 제공 문서가 없는 상황에서 재현 가능한 회원 등록 페이지를 사용한다.
실제 브라우저로 다섯 가지 동작을 확인한 뒤 PRD.md와 직접 입력한 설명으로 로컬 claude가 TC를 작성했다.

```sh
.venv/bin/python -m http.server 8877 --bind 127.0.0.1 --directory tests/fixtures/tc_studio_demo
```

- 페이지: http://localhost:8877
- Studio: http://localhost:8766/tc-studio
- 스위트: TC스튜디오_실사용 / 시트: 회원등록 / 분류: 등록 폼
- 페이지 그룹: tc_studio_demo
- md: testcases/tc_studio_demo/
- 생성 테스트: tests/generated/tc_studio_demo/

테스트 실행 시 브라우저 표시: `HEADED=1 SLOW_MO=350`.
Studio의 기획 정보·TC 생성 화면에서 PRD.md를 업로드하고 초안을 생성한다. 실제 페이지에서 문구를 확인한 후 승인·그룹 매핑·md 반영하고 대시보드 단일 파이프라인에서 해당 그룹을 실행한다.
