# QA 체크리스트

> 스모크 테스트 항목 가이드 + Playwright 테스트 작성 체크리스트

---

## 웹 서비스 스모크 항목

- [ ] 메인 페이지 로딩
- [ ] 로그인/로그아웃
- [ ] 회원가입 (있는 경우)
- [ ] 핵심 페이지 네비게이션
- [ ] 주요 CRUD 기능 (생성/조회/수정/삭제)
- [ ] 검색 기능
- [ ] 권한별 접근 제어

## API 스모크 항목

- [ ] 헬스체크 엔드포인트
- [ ] 인증 API (로그인/토큰 발급)
- [ ] 주요 GET 엔드포인트 응답 확인
- [ ] 주요 POST 엔드포인트 정상 처리
- [ ] 에러 응답 형식 (4xx, 5xx)

## 배포 후 확인 항목

- [ ] SSL 인증서 유효
- [ ] 리다이렉트 정상 동작
- [ ] 정적 리소스 로딩 (이미지, CSS, JS)
- [ ] 콘솔 에러 없음
- [ ] API 응답 시간 정상 범위

---

## Playwright 테스트 작성 체크리스트

> 셀렉터 전략·대기 패턴·Assertion 상세: [`.claude/skills/playwright-best-practices/SKILL.md`](../.claude/skills/playwright-best-practices/SKILL.md)
> 힐링 시 MCP 시각 검증: [`doc/operations/HEALING_GUIDE.md`](../doc/operations/HEALING_GUIDE.md)

- [ ] 셀렉터가 dom_info 기반 (`#id` 우선, 추측 금지)
- [ ] `to_contain_text()` 사용 (`to_have_text()` 공백 위험)
- [ ] URL 검증 시 `re.compile()` 사용 (lambda 금지)
- [ ] `expect()` timeout은 matcher 메서드에 전달
- [ ] 팝업/alert 처리 포함 (발생 여부만 검증)
- [ ] `ENV:` 프리픽스 → `os.environ.get()` + `pytest.skip()`
