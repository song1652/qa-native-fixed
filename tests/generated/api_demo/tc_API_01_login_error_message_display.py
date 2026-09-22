"""
tc_API_01_login_error_message_display.py
- 인증 API 실패(HTTP 500) 시 에러 메시지 표시 검증 — 실패 상세(Failure Inspector) 데모
- BASE_URL, import, 상수를 이 파일에 직접 포함 (공유 헬퍼 금지)
- 테스트 함수명: test_login_error_message_display
- 실제 고객 사이트를 쓰지 않고 이 파일 안에 완결된 로그인 폼을 렌더링하고,
  page.route()로 인증 API 호출을 결정적으로(외부 네트워크 의존 없이) 500으로
  실패시킨다 — 실패 상세 화면에서 스크린샷·콘솔로그·네트워크실패·trace를
  실제로 확인해보기 위한 데모 케이스.
"""
from playwright.sync_api import Page, Route, expect

DEMO_LOGIN_HTML = """
<html>
<body>
  <h1>고객 로그인</h1>
  <form>
    <input id="user_id" placeholder="아이디">
    <input id="password" type="password" placeholder="비밀번호">
    <button id="submit" type="button">로그인</button>
  </form>
  <script>
    document.getElementById('submit').addEventListener('click', () => {
      fetch('https://api.internal.demo/auth/verify')
        .then((res) => {
          if (!res.ok) {
            // 실제 버그: #error-message 엘리먼트를 화면에 만들지 않고 바로 참조함
            document.getElementById('error-message').textContent = '로그인에 실패했습니다. 다시 시도해주세요.';
          }
        })
        .catch((err) => console.error('auth request failed', err));
    });
  </script>
</body>
</html>
"""


def _fail_auth_with_500(route: Route) -> None:
    route.fulfill(status=500, content_type="text/plain", body="Internal Server Error")


def test_login_error_message_display(page: Page) -> None:
    """API_01: 인증 API가 500을 반환하면 에러 메시지가 표시돼야 하는데, 프론트 버그로 표시되지 않는다.

    page.route()로 인증 요청을 가로채 500을 강제한다 — 실제 외부 네트워크에
    의존하면 왕복 시간에 따라 3초 타임아웃 안에 콘솔/네트워크 이벤트가
    기록되지 않을 수 있어(실제로 재현된 문제), 결정적으로 재현한다.

    tc_API_01_login_error_message_display.md의 "테스트 스텝"이 "아이디와
    비밀번호 입력 필드에 값을 입력한다"고 문서화돼 있는데, 이전 버전은
    실제로 입력을 하지 않고 바로 클릭만 했다 — 문서와 코드가 안 맞았고,
    그 결과 영상에도 필드 입력 액션이 전혀 안 담겼다(실제로 확인됨).
    """
    page.route("**/auth/verify", _fail_auth_with_500)
    page.set_content(DEMO_LOGIN_HTML)
    page.fill("#user_id", "demo_user")
    page.fill("#password", "wrong_password")
    page.click("#submit")
    expect(page.locator("#error-message")).to_be_visible(timeout=3000)
