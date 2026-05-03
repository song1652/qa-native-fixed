# Lessons Learned — QA 자동화 실수 패턴

> **독자**: 심의 Agent — 코드 작성·리뷰·힐링 전 자동 참조.
> 같은 실수를 반복하지 않기 위한 **큐레이션된** 패턴 모음.
> 자동 기록 로그는 [lessons_learned_auto.md](lessons_learned_auto.md) 참조.
> **관리 규칙**: 중복 섹션 발견 즉시 병합. Stale 패턴 삭제. 500줄 이상 시 큐레이션 패스 실행.

---

## DirectCloud — 로그인 & 세션

- **병렬 실행 금지**: 계정당 단일 세션. 반드시 `-n 1`
- **login() retry 필수**: `wait_for_url("**/mybox/**")` 단독 호출은 세션 충돌 시 TimeoutError
  ```python
  def login(page, company_code, user_id, password):
      page.goto(BASE_URL)
      page.wait_for_timeout(1000)
      page.fill('[name="company_code"]', company_code)
      page.fill('[name="id"]', user_id)
      page.fill('[name="password"]', password)
      page.click('#new_btn_login')
      try:
          page.wait_for_url("**/mybox/**", timeout=20000)
      except Exception:
          page.goto(BASE_URL)
          page.wait_for_timeout(3000)
          page.fill('[name="company_code"]', company_code)
          page.fill('[name="id"]', user_id)
          page.fill('[name="password"]', password)
          page.click('#new_btn_login')
          page.wait_for_url("**/mybox/**", timeout=30000)
  ```
- **conftest.py 쿨다운**: `tests/generated/directcloud/conftest.py` autouse fixture로 5.0초 간격 강제. '공유 헬퍼 금지' 예외
- **goto 후 즉시 fill 금지**: `page.goto()` → `wait_for_timeout(1000)` → fill 순서 필수
- **wait_for_url timeout 15000 불충분 (23회 반복)**: `wait_for_url("**/mybox/**", timeout=15000)` — DirectCloud 서버 응답 지연으로 반복 실패. **최소 20000, retry 시 30000** 사용 필수
  ```python
  # BAD
  page.wait_for_url("**/mybox/**", timeout=15000)
  # GOOD
  page.wait_for_url("**/mybox/**", timeout=20000)   # 최초 시도
  page.wait_for_url("**/mybox/**", timeout=30000)   # retry 시
  ```
- **click 클릭 불가 오류 (12회 반복)**: `await self._channel.send("click")` 오류는 요소가 visible/enabled 상태가 아닌 채 클릭 시도. 클릭 전 반드시 `wait_for(state='visible')` 또는 `expect(locator).to_be_visible()` 확인
  ```python
  # BAD
  page.locator('#btn').click()
  # GOOD
  btn = page.locator('#btn')
  btn.wait_for(state='visible', timeout=10000)
  btn.click()
  ```
- **wait_for_url 필수**: `networkidle` 단독 부족. `wait_for_url(re.compile(r"/mybox|/recents"), timeout=20000)` 병행
- **AI 팝업 인터셉션**: 로그인 후 `sc-TuwoP` 팝업 → `page.keyboard.press('Escape')` + `wait_for_timeout(300)`
- **storage_state 주의**: 새 로그인 시 기존 state 무효화 가능
- **import re 파일 상단 필수**: login() 내 `re.compile()` 사용 시 함수 바디 import 불충분
- **06_heal.py 반복 호출 금지**: 호출마다 `heal_count` 증가 → `heal_failed` 전락

---

## DirectCloud — 셀렉터 & UI

- **사이드바 ID 없음**: `li#mybox`, `li#sharedbox`, `li#trash` 전부 없음 → `li:has-text("텍스트").first`
  - 메뉴: Home / My Box / 최근파일 / 즐겨찾기 / 주소록 / Shared Box / AI 폴더 / Link History / File Request / Trash / Mail
- **검색창**: `#inputSearch` 없음 → `[placeholder="검색"]`
- **컨텍스트 메뉴 텍스트**: 다운로드 / 복사 / 이동 / **이름변경** / **링크생성** / 삭제 / 즐겨찾기 / 태그
- **#modal-settings**: strict mode — 5개 select 매칭 → `.first` 필수. `wait_for(state='visible', timeout=20000)` (10000 부족)
- **모달 timeout 일반**: `.wait_for(state='visible')` 계열은 기본 20000 이상
- **설정 모달 언어 select**: `#lang` 없음 → 모달 내 모든 `select` 순회하여 언어 옵션 확인
- **존재하지 않는 ID 단언 금지**: `#ch_filesAll`, `#fileuploadBtn` 등 → `.count() > 0` 체크 후 조건부
- **hidden checkbox JS 클릭**: `display:none` checkbox → `page.evaluate("() => document.querySelector('#id').click()")`
- **스토리지 사용량**: `.nav-profile h4`
- **AI 폴더 새 탭**: `li:has-text("AI 폴더")` 클릭 → 새 탭 → `context.expect_page()` 필수
- **AI home 접근**: `li#aihome` 없음 → `page.goto(".../aihome")` 직접 이동
- **contacts CSV**: 다운로드 "현재 주소록 CSV 다운로드", 업로드 "CSV 일괄등록"
- **로그아웃 검증**: `"login" in page.url or has_login_form` 패턴 (URL 타이밍 이슈 방지)
- **항상 통과 assertion 금지**: `count() >= 0`, `is_visible() or True` 패턴은 테스트 가치 없음

---

## DirectCloud — 파일·폴더·컨텍스트 메뉴

- **파일 vs 폴더 CSS**: `li.preview__list-item:not(.folder)` 로 파일만 선택
- **Trash 레이아웃**: table 레이아웃. `li.preview__list-item` 안 됨 → `tbody tr, tr:has(td)`
- **MyBox 빈 계정**: count==0이면 `pytest.skip()`. `.checkbox-list-item`은 항상 존재하므로 빈 상태 감지 금지
- **내용 없으면 skip**: 휴지통·SharedBox 등 조건부 환경 → `if items.count() == 0: pytest.skip("대상 없음")`
- **컨텍스트 메뉴 텍스트 주의**: 삭제 / 이름변경 / 링크생성 (영구삭제 X, 이름바꾸기 X, 링크공유 X)
- **TC303 새 폴더 컨텍스트 메뉴**: `ul.table-files` 하단 아래에서만 나타남. `height: 900` 뷰포트 필수
- **`[class*="listItem"]` 위험**: disabled 항목 매칭 → `li[class*="listItem"]:not(.listItem-checkbox-label-all)` 사용
- **sidebar try/except**: `.first.click()` 도 예외 가능. try/except + `goto()` 폴백
- **dismiss_popups() 금지 케이스**: 파일 상세 패널 사용 중, 링크생성 모달 검증 전 — Escape가 모달을 닫음
- **AI 채팅 2단계 진입**: 사이드바 "AI 폴더" → 새 탭(/ai) → "DirectCloud AI" 클릭 → 채팅창
  - 입력창: `textarea[placeholder*="입력"]`, 전송: `button:has-text("전송")`
- **SharedBox 폴더 진입**: 최상위는 폴더만 존재. `li.preview__list-item.folder` 직접 `.dblclick()` → SPA 무시
  → 내부 `.preview__cover`를 더블클릭해야 진입. `wait_for_timeout(3000)` 필수 (2s 불충분)

---

## 공통 — Locator & Assertion

- **URL 추측 금지**: 존재하는 페이지에서 링크를 찾아 navigate
- **not_to_have_url**: URL 변경 없는 경우 실패 → DOM 변화(요소 소멸)로 검증
- **중복 ID**: `#loading` 등 중복 시 text 출현으로 대기. 탭 구조는 활성 pane으로 스코핑
- **DOM 구조 추측 금지**: `dom_info` 없이 추측 selector 금지
- **strict mode**: `.first` 또는 부모 스코프 제한
- **to_have_class**: `re.compile(r"active")` 필수. 문자열 regex 작동 안 함
- **Playwright matcher에 lambda 금지**: `re.compile()` 사용
- **triple_click 없음**: `click(click_count=3)` 사용
- **동적 콘텐츠 exact count 금지**: `count >= 1` 패턴 사용
- **expect() timeout**: `expect(locator).to_be_visible(timeout=N)` — matcher 메서드에 전달
- **대소문자**: `expect(loc).to_contain_text("TEXT", ignore_case=True)` 필수
- **alert 검증**: 메시지 내용 하드코딩 금지. alert 발생 자체만 검증
- **서브페이지 DOM 확인 필수**: 메인 URL만 분석하면 inputs=0. steps의 서브페이지 URL도 각각 분석

---

## 공통 — 코드 작성

- **미사용 import 금지**: F401. 사용하는 모듈만 import
- **미사용 변수 금지**: F841. 불필요한 할당 제거
- **test_data.json 경로**: `.parent` 4번 필요. `resolve()` 포함 권장
- **test_data.json 인코딩**: `open(path, encoding='utf-8')` 명시 (Windows cp949 기본 → UnicodeDecodeError)
- **test_data.json 키**: `test_data["directcloud"]["key"]` 형식. KeyError 방지 위해 키 존재 확인
- **page.evaluate() arrow function**: return 문 사용 시 `() => { return ...; }` 래핑 필수
- **navigate 중 evaluate 금지**: 클릭 후 이동 예상 시 `wait_for_load_state()` 후 evaluate
- **pytest 모듈 충돌**: 동일 basename 파일 → `__init__.py` 필수
- **items.click() try/except**: count > 0 이후 상호작용도 try/except 필수
- **JS Prompt dialog 이중 처리 금지**: `page.on("dialog", ...)` 핸들러 + `dialog.accept()` 동시 사용 시 "already handled" 오류. `window.prompt` 오버라이드 방식으로 대체: `page.evaluate(f"window.prompt = () => {repr(text)};")`
- **동적 콘텐츠 exact count 단언 금지**: `/dynamic_content` 등 페이지는 row 수가 가변 → `== N` 대신 `>= N` 사용
  ```python
  # BAD — 동적 페이지에서 exact count 실패
  assert count == 3, f"Expected 3 content rows, got {count}"
  # GOOD
  assert count >= 1, f"Expected at least 1 content row, got {count}"
  ```
- **strict mode + 중첩 locator**: `row.locator(".large-10")` 등 부모 row 내에 동일 클래스가 여러 개일 경우 `.first` 필수
- **test_data.json encoding 명시 필수 (12회 반복)**: Windows 환경에서 기본 cp949 인코딩으로 utf-8 파일 읽기 실패. 모든 json 로드 시 `encoding='utf-8'` 명시
  ```python
  # BAD
  with open(path) as f:
      data = json.load(f)
  # GOOD
  with open(path, encoding='utf-8') as f:
      data = json.load(f)
  ```
