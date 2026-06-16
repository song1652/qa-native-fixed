# Lessons Learned (Auto) — 자동 기록 힐링 패턴

> **독자**: 심의 Agent — 힐링 시 보조 참조. 큐레이션 패턴([lessons_learned.md](lessons_learned.md)) 우선 확인 후 이 파일로 최신 패턴 보완.
> **읽는 시점**: `06a_dialog.py`가 DELIBERATION_CONTEXT에 lessons_snapshot으로 자동 주입하므로, Agent가 직접 읽을 필요는 드뭄. 최신 자동 기록 직접 확인 시에만 Read.
> **자동 생성 파일**: `heal_utils.py`의 `append_lessons()`가 힐링 시 자동 기록. 수동 편집 금지.

---

## Locator 오류

- **Locator**: `page.locator(".login-iframe > iframe").wait_for(state="visible", timeout=6000)` -- dom_info 셀렉터 재확인, #id 우선 사용

- **Locator**: `page.locator(".login-iframe > iframe").wait_for(state="visible", timeout=8000)` -- dom_info 셀렉터 재확인, #id 우선 사용

- **Locator**: `expect(page.get_by_text("스탠다드").first).to_be_visible()` -- dom_info 셀렉터 재확인, #id 우선 사용
- **Locator**: `assert page.locator("iframe").is_visible()` -- dom_info 셀렉터 재확인, #id 우선 사용
- **Locator**: `expect(page.get_by_text("라이트").first).to_be_visible()` -- dom_info 셀렉터 재확인, #id 우선 사용
- **Locator**: `expect(page.get_by_text("BEST").first).to_be_visible()` -- dom_info 셀렉터 재확인, #id 우선 사용
- **Locator**: `self._sync(self._impl_obj.get_attribute(name=name, timeout=timeout))` -- dom_info 셀렉터 재확인, #id 우선 사용
- **Locator**: `expect(page.get_by_text("환불 규정")).to_be_visible()` -- dom_info 셀렉터 재확인, #id 우선 사용
- **Locator**: `assert numeric_elements.count() > 0` -- dom_info 셀렉터 재확인, #id 우선 사용
- **Locator**: `expect(page.get_by_text("9,900원")).to_be_visible()` -- dom_info 셀렉터 재확인, #id 우선 사용

- **Locator**: `assert page.locator('ul.table-files').is_visible(), "파일 목록 영역(ul.table-files)이 표시되지 않습니다"` -- dom_info 셀렉터 재확인, #id 우선 사용
- **Locator**: `assert file_list.count() > 0, "파일 목록 영역을 찾을 수 없습니다"` -- dom_info 셀렉터 재확인, #id 우선 사용
- **Locator**: `assert comment_count.count() > 0, "파일 목록에 코멘트 수 배지가 표시되지 않습니다"` -- dom_info 셀렉터 재확인, #id 우선 사용
- **Locator**: `assert file_list.count() > 0, "MyBox 파일 목록이 표시되지 않습니다"` -- dom_info 셀렉터 재확인, #id 우선 사용
- **Locator**: `assert page.locator('li.preview__list-item').count() > 0 or \` -- dom_info 셀렉터 재확인, #id 우선 사용
- **Locator**: `assert new_folder_menu.count() > 0, (` -- dom_info 셀렉터 재확인, #id 우선 사용
- **Locator**: `assert username_display.count() > 0, "설정 모달에 사용자 정보가 표시되지 않습니다"` -- dom_info 셀렉터 재확인, #id 우선 사용
- **Locator**: `assert photo_nav.count() > 0, "공유박스 사이드바에서 Photo 항목을 찾을 수 없습니다"` -- dom_info 셀렉터 재확인, #id 우선 사용

- **Locator**: `assert "login" not in new_url or current_url == new_url or page.locator('li#mybox').count() > 0` -- dom_info 셀렉터 재확인, #id 우선 사용
- **Locator**: `E   AssertionError: assert False` -- dom_info 셀렉터 재확인, #id 우선 사용
- **Locator**: `await self._channel.send("click", self._timeout, locals_to_params(locals()))` -- dom_info 셀렉터 재확인, #id 우선 사용
- **Locator**: `E   assert False` -- dom_info 셀렉터 재확인, #id 우선 사용

- **Locator (반복 패턴)**: `expect(...).to_be_visible()` / `assert locator.is_visible()` 실패 다수 — dom_info 셀렉터 재확인, `#id` 우선 사용. 존재하지 않는 요소에 단언 금지, `.count() > 0` 체크 후 조건부 실행 (힐링 자동 기록 항목 ~80건 압축)

## Assertion 오류

- **Assertion**: `assert len(errors) == 0, f"Console errors found: {errors}"` -- 실제 페이지 텍스트/상태로 기댓값 수정

- **Assertion**: `expect(page).to_have_url(re.compile(r"/mybox"))` -- 실제 페이지 텍스트/상태로 기댓값 수정
- **Assertion**: `expect(page).to_have_url(re.compile(r"/recents"), timeout=15000)` -- 실제 페이지 텍스트/상태로 기댓값 수정

- **Assertion**: `assert moved_x > 10 or moved_y > 10, (` -- 실제 페이지 텍스트/상태로 기댓값 수정

- **Assertion**: `assert abs(new_cy - initial_cy) > 10, (` -- 실제 페이지 텍스트/상태로 기댓값 수정
- **Assertion**: `assert idx_one > idx_three, f"Expected 'One' after 'Three', got order: {texts}"` -- 실제 페이지 텍스트/상태로 기댓값 수정
- **Assertion**: `assert "In a list!" in text, f"Expected 'In a list!' in shadow DOM text, got: {text!r}"` -- 실제 페이지 텍스트/상태로 기댓값 수정
- **Assertion**: `assert count >= 5, f"Expected at least 5 list items, got {count}"` -- 실제 페이지 텍스트/상태로 기댓값 수정
- **Assertion**: `E   AssertionError: Width should increase` -- 실제 페이지 텍스트/상태로 기댓값 수정
- **Assertion**: `assert "In a list!" in text or "list" in text.lower(), f"Expected list content, got: {text}"` -- 실제 페이지 텍스트/상태로 기댓값 수정

## Timeout 오류

- **Timeout**: `page.wait_for_url("**/mypage/order/cart/detail/**", timeout=10000)` -- expect(..., timeout=10000) 또는 wait_for_selector 추가

- **Timeout**: `page.wait_for_url(re.compile(r"/mybox"), timeout=20000)` -- expect(..., timeout=10000) 또는 wait_for_selector 추가

- **Timeout**: `page.wait_for_url("**/login**", timeout=20000)` -- expect(..., timeout=10000) 또는 wait_for_selector 추가

- **Timeout**: `page.wait_for_url("**/mybox/**", timeout=15000)` -- expect(..., timeout=10000) 또는 wait_for_selector 추가

- **Timeout**: `async with self.expect_navigation(` -- expect(..., timeout=10000) 또는 wait_for_selector 추가

- **Timeout**: `raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None` -- expect(..., timeout=10000) 또는 wait_for_selector 추가

## URL 오류

## JS평가 오류

## Python런타임 오류

- **Python런타임**: `E   NameError: name 're' is not defined. Did you forget to import 're'` -- test_data 키/import/변수명 확인

- **Python런타임**: `E   KeyError: 'search_keyword'` -- test_data 키/import/변수명 확인

## Playwright일반 오류

- **Playwright일반**: `raise Error(` -- 브라우저 상태 확인, 페이지 닫힘/크래시 대응

## 기타

- **기타**: `E   UnicodeDecodeError: 'cp949' codec can't decode byte 0xec in position 589: illegal multibyte sequence` -- 
