# Lessons Learned — QA 자동화 실수 패턴

> **독자**: 심의 Agent — 코드 작성·리뷰·힐링 전 자동 참조.
> 같은 실수를 반복하지 않기 위한 **큐레이션된** 패턴 모음.
> 자동 기록 로그는 [lessons_learned_auto.md](lessons_learned_auto.md) 참조.
> **관리 규칙**: 중복 섹션 발견 즉시 병합. Stale 패턴 삭제. 500줄 이상 시 큐레이션 패스 실행.

---

## SauceDemo 장바구니 패턴

- **`[data-test="cart-item"]` 존재하지 않음**: SauceDemo `/cart.html`의 장바구니 아이템 선택자는 `[data-test="cart-item"]`이 아니라 `.cart_item` CSS 클래스. `data-test` 속성이 없으므로 반드시 `.cart_item` 사용.
- **add-to-cart 후 배지 검증 필수**: 장바구니 이동 전 `expect(page.locator('[data-test="shopping-cart-badge"]')).to_contain_text("1")` 로 아이템이 실제 추가됐음을 확인. 이 단계 없으면 빈 장바구니로 이동 후 `.cart_item` timeout 발생.
- **login 후 `wait_for_url` 필수**: `page.wait_for_load_state("networkidle")` 단독으로는 로그인 → /inventory 전환을 보장하지 못함. `page.wait_for_url(re.compile(r"/inventory"), timeout=15000)` + `networkidle` 병행 사용.
  ```python
  # BAD
  page.locator('[data-test="login-button"]').click()
  page.wait_for_load_state("networkidle")
  # GOOD
  page.locator('[data-test="login-button"]').click()
  page.wait_for_url(re.compile(r"/inventory"), timeout=15000)
  page.wait_for_load_state("networkidle")
  ```
- **장바구니 이동 후 `wait_for_url` 필수**: `[data-test="shopping-cart-link"]` 클릭 후 `page.wait_for_url(re.compile(r"/cart"), timeout=10000)` 추가.

---

## 로그인 & 세션

- **로그인 후 랜딩 URL 다양성**: SPA 앱 환경에 따라 로그인 성공 후 `/mybox/`가 아닌 `/home` 등 다른 경로로 이동할 수 있음. wait_for_url 패턴에 가능한 랜딩 경로를 모두 포함할 것 (`re.compile(r"/(home|mybox|recents)")`)
- **환경별 BASE_URL 혼용 금지**: 파이프라인 URL과 테스트 BASE_URL은 반드시 동일 환경 사용. 환경이 다르면 테스트 계정 자격증명이 동작하지 않아 alert 발생

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
- **conftest.py 쿨다운**: `tests/generated/{group}/conftest.py` autouse fixture로 5.0초 간격 강제. '공유 헬퍼 금지' 예외
- **goto 후 즉시 fill 금지**: `page.goto()` → `wait_for_timeout(1000)` → fill 순서 필수
- **wait_for_url timeout 15000 불충분 (23회 반복)**: `wait_for_url("**/mybox/**", timeout=15000)` — 서버 응답 지연으로 반복 실패. **최소 20000, retry 시 30000** 사용 필수
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
- **SPA 팝업 인터셉션**: 로그인 후 고정 z-index 팝업(`sc-TuwoP` 등) → `page.keyboard.press('Escape')` + `wait_for_timeout(300)`
- **storage_state 주의**: 새 로그인 시 기존 state 무효화 가능
- **import re 파일 상단 필수**: login() 내 `re.compile()` 사용 시 함수 바디 import 불충분
- **06_heal.py 반복 호출 금지**: 호출마다 `heal_count` 증가 → `heal_failed` 전락

---

## 셀렉터 & UI

- **사이드바 ID 우선 사용**: `li#mybox`, `li#sharedbox`, `li#trash`, `li#home`, `li#recents` 등 고유 ID 있음. `li:has-text()` 대신 ID 선택자 사용 권장
  - 메뉴: `li#home`(Home) / `li#mybox`(My Box) / `li#recents`(최근파일) / `li#sharedbox`(Shared Box) / `li#trash`(Trash)
- **검색창**: `#inputSearch` 없음 → `[placeholder="검색"]`
- **컨텍스트 메뉴 텍스트**: 다운로드 / 복사 / 이동 / **이름변경** / **링크생성** / 삭제 / 즐겨찾기 / 태그
- **#modal-settings**: strict mode — 5개 select 매칭 → `.first` 필수. `wait_for(state='visible', timeout=20000)` (10000 부족)
- **모달 timeout 일반**: `.wait_for(state='visible')` 계열은 기본 20000 이상
- **설정 모달 언어 select**: `#lang` 없음 → 모달 내 모든 `select` 순회하여 언어 옵션 확인
- **존재하지 않는 ID 단언 금지**: `#ch_filesAll`, `#fileuploadBtn` 등 → `.count() > 0` 체크 후 조건부
- **hidden checkbox JS 클릭**: `display:none` checkbox → `page.evaluate("() => document.querySelector('#id').click()")`
- **스토리지 사용량**: `.nav-profile h4`
- **새 탭으로 열리는 메뉴 항목**: 클릭 시 새 탭 열림 → `context.expect_page()` 필수
- **ID 없는 메뉴 진입**: `li#aihome` 등 ID 없는 경우 → `page.goto(".../aihome")` 직접 이동
- **contacts CSV**: 다운로드 "현재 주소록 CSV 다운로드", 업로드 "CSV 일괄등록"
- **로그아웃 검증**: `"login" in page.url or has_login_form` 패턴 (URL 타이밍 이슈 방지)
- **항상 통과 assertion 금지**: `count() >= 0`, `is_visible() or True` 패턴은 테스트 가치 없음
- **클릭 후 변화 검증 시 클릭 대상 자체 count 금지**: `page.locator('[data-testid="forgot-password-button"]').count() > 0` 를 클릭 후 변화 조건으로 사용하면, 버튼이 클릭 전후 모두 존재하므로 항상 True → `or` 연결 시 전체 assertion이 무효화됨. 클릭 대상 요소 외의 **새로 출현하는 요소** 또는 URL 변화로만 검증할 것

---

## 파일·폴더·컨텍스트 메뉴

- **파일 vs 폴더 CSS**: `li.preview__list-item:not(.folder)` 로 파일만 선택
- **Trash 레이아웃**: table 레이아웃. `li.preview__list-item` 안 됨 → `tbody tr, tr:has(td)`
- **MyBox 빈 계정**: count==0이면 `pytest.skip()`. `.checkbox-list-item`은 항상 존재하므로 빈 상태 감지 금지
- **내용 없으면 skip**: 휴지통·SharedBox 등 조건부 환경 → `if items.count() == 0: pytest.skip("대상 없음")`
- **컨텍스트 메뉴 텍스트 주의**: 삭제 / 이름변경 / 링크생성 (영구삭제 X, 이름바꾸기 X, 링크공유 X)
- **TC303 새 폴더 생성**: 우클릭 컨텍스트 메뉴 방식 동작 안 함. `[data-test-id="toolbar-create-new"]` 버튼 → 드롭다운 `li:has-text("새 폴더")` 클릭 → `#modal-new-folder` 모달 → `input[name="name"]` 입력 → `button.btn-success:has-text("생성")` 클릭
- **파일 목록 컨테이너**: `ul.table-files` TEST 환경에 없음. 실제 선택자 `#files`(전체 파일 영역), `.table-wrap`(목록 컨테이너). 빈 폴더여도 `#files`는 항상 visible
- **SPA 렌더링 지연**: networkidle 후에도 `#files` 렌더링에 추가 시간 필요. `page.wait_for_selector('#files', state='visible', timeout=15000)` 사용. `is_visible()` 직접 assert 금지
- **설정 모달 열기**: `page.mouse.click(1251, 27)` 좌표는 불안정 → `.nav-profile` 클릭 사용. 사용자명이 "게스트"가 아닌 경우 `has-text("게스트")` 어설션 실패 → 모달 visible만 확인
- **SharedBox 빈 경우**: 서브폴더(Photo 등)가 없을 수 있음. 특정 폴더 존재에 의존하는 assert 대신 페이지 접근 확인으로 대체
- **`[class*="listItem"]` 위험**: disabled 항목 매칭 → `li[class*="listItem"]:not(.listItem-checkbox-label-all)` 사용
- **sidebar try/except**: `.first.click()` 도 예외 가능. try/except + `goto()` 폴백
- **dismiss_popups() 금지 케이스**: 파일 상세 패널 사용 중, 링크생성 모달 검증 전 — Escape가 모달을 닫음
- **AI 채팅 2단계 진입**: 사이드바 AI 메뉴 → 새 탭(/ai) → AI 채팅 버튼 클릭 → 채팅창
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
- **test_data.json 키**: `test_data["target"]["key"]` 형식. KeyError 방지 위해 키 존재 확인
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

---

## React SPA 심화 패턴

### 절대 금지 안티패턴

| 안티패턴 | 결과 | 올바른 방법 |
|----------|------|------------|
| `page.evaluate("el.remove()")` DOM 직접 제거 | React 앱 전체 파괴 | `dismiss_tip_popup()` 좌표 클릭 |
| `dispatchEvent(new MouseEvent('click'))` | `isTrusted=false` → React 무시 | `page.mouse.click(좌표)` |
| `.popover` selector로 Tip 팝업 타겟 | 요소 못 찾음 | z-index 기반 DOM 탐색 |
| `set_input_files()` headless | 파일 선택 실패 | API 직접 호출 방식 |
| `page.mouse.click(좌표)` for 모달 submit | 클릭 불안정 | `locator.click()` 네이티브 |
| `wait_for_load_state('domcontentloaded')` 후 요소 확인 | SPA 렌더링 전 → 요소 없음 | `networkidle` 필수 |
| `locator.is_visible(timeout=N)` 로 대기 | timeout 무시, 즉시 반환 | `wait_for(state='visible', timeout=N)` |
| `filter(has_text='A, B')` 쉼표 OR 시도 | 리터럴로 해석 | `filter(has_text=re.compile(r'A\|B'))` |

- **`is_visible()`은 timeout을 지원하지 않는다**: `is_visible(timeout=10000)` → timeout 무시, 즉시 `False` 반환.
  SPA 비동기 렌더링 대기는 반드시 `wait_for(state='visible', timeout=N)` 또는 `expect(locator).to_be_visible(timeout=N)` 사용

- **삭제 확인은 `wait_for(state='hidden')` 필수**: `is_visible() == False` 단독 체크는 SPA 리렌더링 타이밍에 따라 flaky
  ```python
  # BAD — 타이밍 flaky
  assert not row.is_visible()
  # GOOD
  page.wait_for_load_state('networkidle')
  row.wait_for(state='hidden', timeout=15000)
  assert not row.is_visible()
  ```

- **쉼표 구분 selector는 OR가 아님**: Playwright Python에서 `filter(has_text='ログアウト, 로그아웃')`은 리터럴 문자열 탐색
  ```python
  # BAD
  page.locator('button').filter(has_text='ログアウト, 로그아웃')
  # GOOD
  page.get_by_role('button', name=re.compile(r'ログアウト|로그아웃|Logout'))
  ```

- **로그아웃 후 URL 미변경 시 쿠키 삭제 fallback**:
  ```python
  # URL이 변경되지 않으면 쿠키 삭제 + reload로 강제 로그아웃 확인
  page.context.clear_cookies()
  page.reload()
  page.wait_for_load_state('networkidle')
  on_login = '/login' in page.url or page.locator('input[name="id"]').first.is_visible()
  assert on_login
  ```

- **로그아웃 3단계 전략 (60초 제한)**: SPA 앱 로그아웃은 환경·플랜별 UI가 달라 단일 전략 불가. 각 전략 timeout을 2~3초로 짧게 설정. 전략 순서: (1) 직접 로그아웃 링크 2초 → (2) 프로필→설정→로그아웃 최대 2회 → (3) `/auth/logout` URL 직접 이동. 전략 3은 거의 항상 성공하므로 앞 전략에서 시간 낭비하지 않는 것이 핵심

- **이름변경 input 탐색**: `input[name="name"]` 금지 — 검색박스, 새폴더 모달 등 여러 곳에서 중복 사용됨. 반드시 **파일 행 내부** `row.locator('input').first` 우선 탐색
  ```python
  # BAD — 검색박스나 새폴더 모달 input과 충돌
  page.locator('input[name="name"]').first.fill(new_name)
  # GOOD — 행 내부 인라인 input 우선
  inline_input = row.locator('input').first
  inline_input.wait_for(state='visible', timeout=3000)
  inline_input.fill(new_name)
  inline_input.press('Enter')
  ```

- **SPA 로그인 후 URL 다양한 패턴**: 환경에 따라 랜딩 URL이 다름. `/mybox/`만 체크하면 일부 환경에서 실패
  ```python
  # BAD
  page.wait_for_url(re.compile(r'/mybox/'), timeout=10000)
  # GOOD — 4가지 패턴 모두 허용
  page.wait_for_url(re.compile(r'/(mypage|home|top|files|drive)'), timeout=30000)
  ```

- **`test.skip()` 대신 데이터 보장 헬퍼 사용**: 파일/폴더 없으면 skip하지 말고 API 업로드로 전제조건을 테스트 내에서 자동 충족. `pytest.skip()`은 환경 가드(IS_REAL, 플랜 미지원)에만 사용

- **SPA 이동 후 Tip 팝업 + 대기 필수**: SPA 내 메뉴 클릭 후 `networkidle` + `wait_for_timeout(1000~2000)` + `dismiss_tip_popup()` 순서 필수. `domcontentloaded` 직후 파일 목록 탐색 시 렌더링 미완료로 0건 반환

- **conftest.py 이벤트 핸들러 KeyError**: `context.close()` 후 미처리 console/network 이벤트가 늦게 발화해 이미 `pop()`된 `test_name` 키에 접근 → `KeyError`. 가드 조건(`and test_name in _console_logs`) 필수
  ```python
  # BAD
  page.on("console", lambda msg: _console_logs[test_name].append({...}) if msg.type in ("error", "warning") else None)
  # GOOD
  page.on("console", lambda msg: _console_logs[test_name].append({...}) if msg.type in ("error", "warning") and test_name in _console_logs else None)
  ```

- **06_heal.py PosixPath + str 연산 오류**: `gen_path / f["test_name"] + ".py"` → `TypeError`. 문자열 연결 후 Path 연산이 아니라 괄호로 분리: `gen_path / (f["test_name"] + ".py")`

## 리포트 생성 (report_html.py)

- **Playwright 트레이스 이벤트 타입**: `type == "action"` 이벤트는 존재하지 않음. 실제 포맷은 `type == "before"` (`callId`, `startTime`, `class`, `method`) + `type == "after"` (`callId`, `endTime`) 쌍. callId로 매칭 후 `endTime - startTime`으로 duration 계산. `before` 이벤트에 `title` 필드가 있으면 우선 사용 (Expect 등).
- **YAML 없는 추가 TC 렌더링 누락**: `test_results`가 `test_cases`보다 많을 때 (데모 TC 등 YAML 없이 추가된 파일) `_build_rows_html`에서 test_cases 루프가 끝난 후 잔여 `test_items[len(test_cases):]`를 별도로 렌더링해야 함. 그렇지 않으면 아티팩트 패널이 리포트에 나타나지 않음.

## 파이프라인 인프라 (scripts/)

- **write_state() RMW 원자성**: `read_state()` + `write_state()` 사이에 락이 없으면 두 프로세스가 동시에 읽고 먼저 쓴 데이터를 나중 프로세스가 덮어씀. `write_state()` 내부에서 락 파일을 획득하고 검증·쓰기를 락 보호 영역 안에서 수행해야 함. 단, 락 보유 중 `read_state()`를 호출하면 동일 락을 재획득하려다 deadlock 발생 → `_validate_step_transition_locked()`처럼 파일 직접 읽기 사용.

- **classify_error Timeout/Locator 우선순위**: Playwright 타임아웃 메시지에는 항상 "waiting for locator" 텍스트가 포함되므로 Locator 패턴 매칭이 우선되면 모든 타임아웃이 Locator로 오분류됨. 해결책: Timeout 패턴 먼저 확인, 특히 `"ms exceeded"` 키워드 포함 여부로 명시적 타임아웃 식별.

- **`--only-failed` 구현**: `05_execute.py`에서 `sys.argv` 문자열 파싱은 알 수 없는 플래그를 사일런트 무시함. `argparse`로 전환하면 unrecognized argument에서 자동으로 non-zero exit. `--only-failed` 시 `execution_result.json_report_path`의 이전 JSON 리포트를 `parse_results()`로 파싱하여 failed nodeids만 추출 후 pytest에 직접 전달.

- **heal_count 카운터 보존**: 병렬 파이프라인에서 힐링 카운터를 `heal_context.json`에 저장하면, 이 파일이 힐링 완료 시 삭제되어 다음 재실행에서 MAX_HEAL을 우회하는 문제 발생. `pipeline.json`에 `heal_count`를 저장하여 파일 삭제와 무관하게 카운터를 보존해야 함.

## SauceDemo 셀렉터 패턴

- **`.cart_item` vs `[data-test="cart-item"]`**: SauceDemo 장바구니 페이지의 장바구니 아이템 컨테이너는 `[data-test="cart-item"]`이 존재하지 않음. 실제 CSS class인 `.cart_item`을 사용해야 함. `data-test` 목록: `inventory-item`, `cart-list`, `item-quantity` 등이 올바른 속성.
- **SauceDemo headless 호환 확인**: `/inventory.html`, `/cart.html` 등 인증 없이 접근하면 로그인 페이지로 리다이렉트됨. 각 테스트에서 `BASE_URL`에 먼저 로그인 후 진행해야 함.
