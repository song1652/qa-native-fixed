"""
Step 1 -- 페이지 DOM 분석
LLM 없음. Playwright로 직접 DOM 추출.
결과를 state.json의 dom_cache_key에 참조 저장.

Claude Code는 이 스크립트 실행 후
dom_info를 읽고 테스트 전략(plan)을 직접 수립해서 state.json에 저장한다.
"""
import asyncio
import re
import time
import sys
from pathlib import Path
from playwright.async_api import async_playwright
from _paths import (
    PIPELINE_STATE, DOM_CACHE_DIR,
    read_state, update_state,
    get_cached_dom, save_dom_cache, url_cache_key,
)
from _pipeline_registry import Step  # P68: Step 상수 사용 — 문자열 리터럴 대신

_DOM_HELPERS_JS = (Path(__file__).parent / "dom_helpers.js").read_text(encoding="utf-8")


def _js(inner: str) -> str:
    """dom_helpers.js를 앞에 주입하고 IIFE로 래핑."""
    return "() => {\n" + _DOM_HELPERS_JS + "\n" + inner + "\n}"


# ---------------------------------------------------------------------------
# DOM 추출 JS -- analyze_all() 공유
# ---------------------------------------------------------------------------
DOM_EXTRACT_JS = _js("""
    // ── 다중 셀렉터 전략 추출 ─────────────────────────────────────
    function getSelectors(el) {
        const s = {};
        const tag = el.tagName.toLowerCase();
        const text = (el.innerText || el.textContent || el.value || '').trim().slice(0, 60);

        // 1. id (가장 안정적)
        if (el.id) s.id = '#' + el.id;

        // 2. data-testid / data-test / data-cy / data-qa (실제 속성명 사용)
        let testidAttr = null, testidVal = null;
        for (const attr of ['data-testid', 'data-test', 'data-cy', 'data-qa']) {
            const v = el.getAttribute(attr);
            if (v) { testidAttr = attr; testidVal = v; break; }
        }
        if (testidAttr) s.testid = `[${testidAttr}="${esc(testidVal)}"]`;

        // 3. aria-label (접근성 기반, 변경에 강함)
        const ariaLabel = el.getAttribute('aria-label');
        if (ariaLabel) s.aria_label = `[aria-label="${esc(ariaLabel)}"]`;

        // 4. role + name (Playwright getByRole 용)
        const role = el.getAttribute('role');
        if (role && ariaLabel) s.role = `${role}[name="${esc(ariaLabel)}"]`;
        else if (role) s.role = `[role="${role}"]`;

        // 5. placeholder (입력 필드)
        if (el.placeholder) s.placeholder = `[placeholder="${esc(el.placeholder)}"]`;

        // 6. name 속성
        if (el.name) s.name = `[name="${esc(el.name)}"]`;

        // 7. text (버튼·링크·레이블)
        if (text && ['button','a','label','h1','h2','h3','li','span','td','th'].includes(tag))
            s.text = text;

        // 8. CSS (대문자 포함 해시 클래스 제외, ng-/js- 접두사 제외)
        const cls = [...el.classList]
            .filter(c => !c.match(/[A-Z]/) && !c.match(/^(ng-|js-)/) && c.length > 0)
            .slice(0, 2).join('.');
        if (cls) s.css = tag + '.' + cls;

        // 9. XPath (id/testid/name 우선, 없으면 조상 체인으로 id 탐색)
        if (el.id) {
            s.xpath = `//*[@id="${esc(el.id)}"]`;
        } else if (testidAttr) {
            s.xpath = `//*[@${testidAttr}="${esc(testidVal)}"]`;
        } else if (el.name) {
            s.xpath = `//*[@name="${esc(el.name)}"]`;
        } else if (ariaLabel) {
            s.xpath = `//*[@aria-label="${esc(ariaLabel)}"]`;
        } else {
            // 조상 체인에서 id 있는 노드 탐색 (최대 5단계)
            let cur = el.parentNode;
            let depth = 0;
            let idAncestor = null;
            const midPath = [];
            while (cur && cur !== document && cur !== document.body && depth < 5) {
                if (cur.id) { idAncestor = `//*[@id="${esc(cur.id)}"]`; break; }
                const sibs = cur.parentNode
                    ? [...cur.parentNode.children].filter(c => c.tagName === cur.tagName)
                    : [];
                midPath.unshift(`/${cur.tagName.toLowerCase()}[${sibs.indexOf(cur) + 1}]`);
                cur = cur.parentNode; depth++;
            }
            const elSibs = el.parentNode
                ? [...el.parentNode.children].filter(c => c.tagName === el.tagName)
                : [];
            const elIdx = elSibs.indexOf(el) + 1;
            if (idAncestor) {
                s.xpath = idAncestor + midPath.join('') + `/${tag}[${elIdx}]`;
            }
            // 조상 id 없으면 xpath 생략 (불안정)
        }

        return s;
    }

    // ── inputs (visible + hidden 모두) ───────────────────────────
    const inputs = [...document.querySelectorAll('input:not([type=hidden]), textarea, select')]
        .map(el => ({
            selectors: getSelectors(el),
            type:      el.type || el.tagName.toLowerCase(),
            visible:   isVisible(el),
            required:  el.required,
            disabled:  el.disabled,
            value:     el.value?.slice(0, 50) || ''
        }));

    // ── buttons (visible + hidden 모두) ──────────────────────────
    const buttons = [...document.querySelectorAll(
        'button, input[type=submit], input[type=button], [role=button], [role=menuitem]'
    )].map(el => ({
        selectors: getSelectors(el),
        text:      (el.innerText || el.textContent || el.value || '').trim().slice(0, 60),
        type:      el.type || 'button',
        visible:   isVisible(el),
        disabled:  el.disabled || el.getAttribute('aria-disabled') === 'true'
    }));

    // ── 숨겨진 인터랙티브 요소 (모달·드롭다운·메뉴 등) ───────────
    const hiddenElements = [...document.querySelectorAll(
        '[role="dialog"], [role="menu"], [role="tooltip"], [role="listbox"],' +
        '.modal, .dropdown-menu, .popup, .popover, [class*="modal"], [class*="dialog"]'
    )].filter(el => !isVisible(el))
      .map(el => ({
          selectors: getSelectors(el),
          tag:       el.tagName.toLowerCase(),
          role:      el.getAttribute('role') || '',
          trigger:   el.getAttribute('aria-labelledby') || el.getAttribute('data-trigger') || 'unknown',
          children_count: el.querySelectorAll('button, input, a, [role=menuitem]').length,
          children: [...el.querySelectorAll('button, input, a, [role=menuitem], li')]
              .slice(0, 10)
              .map(c => ({
                  tag:  c.tagName.toLowerCase(),
                  text: (c.innerText || c.textContent || '').trim().slice(0, 40),
                  selectors: getSelectors(c)
              }))
      })).slice(0, 30);

    // ── 에러·상태 영역 ────────────────────────────────────────────
    const errors = [...document.querySelectorAll(
        '[role=alert], [role=status], .error, .alert, .message, .invalid-feedback,' +
        '[class*=error], [class*=alert], [class*=warning], [aria-live]'
    )].map(el => ({
        selectors: getSelectors(el),
        role:      el.getAttribute('role') || 'unknown',
        live:      el.getAttribute('aria-live') || '',
        text:      (el.innerText || '').trim().slice(0, 80),
        visible:   isVisible(el)
    })).slice(0, 30);

    // ── 링크 ─────────────────────────────────────────────────────
    const links = [...document.querySelectorAll('a[href]')]
        .filter(a => (a.innerText || '').trim())
        .map(a => ({
            selectors: getSelectors(a),
            text:      a.innerText.trim().slice(0, 50),
            href:      a.href,
            visible:   isVisible(a)
        })).slice(0, 50);

    // ── 네비게이션 li 항목 (사이드바·메뉴·파일목록) ──────────────
    const navItems = [...document.querySelectorAll(
        'nav li, [role="navigation"] li, aside li, .sidebar li,' +
        '[role="menuitem"], [role="treeitem"], [role="listitem"]'
    )].filter(el => (el.innerText || el.textContent || '').trim())
      .map(el => ({
          selectors: getSelectors(el),
          text:      (el.innerText || el.textContent || '').trim().slice(0, 60),
          visible:   isVisible(el),
          href:      el.querySelector('a')?.href || ''
      })).slice(0, 50);

    // ── UI 컴포넌트 ───────────────────────────────────────────────
    const components = [];

    document.querySelectorAll('[role="tab"], [data-toggle="tab"], .nav-link').forEach(el => {
        components.push({
            type: 'tab', selectors: getSelectors(el),
            text: (el.innerText || el.textContent || '').trim().slice(0, 50),
            active: el.classList.contains('active') || el.getAttribute('aria-selected') === 'true',
            visible: isVisible(el)
        });
    });

    document.querySelectorAll('[role="checkbox"], [role="radio"], [type="checkbox"], [type="radio"]').forEach(el => {
        components.push({
            type: el.getAttribute('role') || el.type,
            selectors: getSelectors(el),
            label: el.getAttribute('aria-label') || el.closest('label')?.textContent?.trim()?.slice(0, 50) || '',
            checked: el.checked || el.getAttribute('aria-checked') === 'true',
            visible: isVisible(el)
        });
    });

    document.querySelectorAll('[role="tree"]').forEach(el => {
        const items = el.querySelectorAll('[role="treeitem"]');
        components.push({
            type: 'tree', selectors: getSelectors(el),
            itemCount: items.length,
            items: [...items].slice(0, 10).map(i => ({
                text: i.textContent?.trim()?.slice(0, 50),
                expanded: i.getAttribute('aria-expanded')
            }))
        });
    });

    document.querySelectorAll('.modal, [role="dialog"]').forEach(el => {
        components.push({
            type: 'modal', selectors: getSelectors(el),
            visible: isVisible(el),
            labelledby: el.getAttribute('aria-labelledby') || ''
        });
    });

    document.querySelectorAll('[role="listbox"], select, [class*="select__control"]').forEach(el => {
        components.push({
            type: 'select', selectors: getSelectors(el),
            visible: isVisible(el),
            options: [...el.querySelectorAll('option, [role="option"]')]
                .slice(0, 10).map(o => o.textContent?.trim())
        });
    });

    // ── ID 요소 전체 목록 (visible + hidden) ─────────────────────
    const idElements = [...document.querySelectorAll('[id]')]
        .map(el => ({
            id:      el.id,
            tag:     el.tagName.toLowerCase(),
            role:    el.getAttribute('role') || '',
            visible: isVisible(el),
            text:    (el.innerText || el.textContent || '').trim().slice(0, 40)
        })).slice(0, 150);

    // ── data-testid 요소 전체 목록 ───────────────────────────────
    const testidElements = [...document.querySelectorAll(
        '[data-testid], [data-test], [data-cy], [data-qa]'
    )].map(el => {
        let attr = null, val = null;
        for (const a of ['data-testid', 'data-test', 'data-cy', 'data-qa']) {
            const v = el.getAttribute(a); if (v) { attr = a; val = v; break; }
        }
        return {
            attr,
            testid:  val,
            selector: `[${attr}="${esc(val)}"]`,
            tag:     el.tagName.toLowerCase(),
            text:    (el.innerText || el.textContent || '').trim().slice(0, 40),
            visible: isVisible(el)
        };
    }).slice(0, 50);

    return {
        title:          document.title,
        url:            location.href,
        inputs,
        buttons,
        errors,
        links,
        navItems,
        hidden_elements: hiddenElements,
        components,
        idElements,
        testidElements,
        forms_count:    document.querySelectorAll('form').length,
        selector_note:  'selectors 우선순위: id > testid > aria_label > placeholder > name > text > css > xpath'
    };
""")


# ---------------------------------------------------------------------------
# 우클릭 후보 셀렉터 목록 -- 타입별 첫 번째 visible 요소만 시도
# ---------------------------------------------------------------------------
CONTEXTMENU_CANDIDATES = [
    '[role="treeitem"]',
    '[role="row"]',
    '[role="gridcell"]',
    '[role="listitem"]',
    '[role="article"]',
    'tr',
    'td',
    'li',
    'img',
    '[class*="item"]:not(body)',
    '[class*="file"]',
    '[class*="card"]',
    '[class*="row"]:not(body)',
    '[class*="node"]',
    '[class*="entry"]',
]

# ---------------------------------------------------------------------------
# 우클릭 후 나타난 컨텍스트 메뉴 캡처 JS
# ---------------------------------------------------------------------------
CONTEXTMENU_CAPTURE_JS = _js("""
    // 컨텍스트 메뉴 패턴 — role 기반 + 클래스명 패턴
    const query = [
        '[role="menu"] [role="menuitem"]',
        '[role="menu"] [role="separator"]',
        '[role="menu"] li',
        '[role="menu"] a',
        '[role="menu"] button',
        '[role="menubar"] [role="menuitem"]',
        '[class*="context-menu"] li',
        '[class*="context-menu"] a',
        '[class*="context-menu"] button',
        '[class*="contextmenu"] li',
        '[class*="contextmenu"] a',
        '[class*="contextmenu"] button',
        '[class*="ctx-menu"] li',
        '[class*="ctx-menu"] button',
        '[class*="right-click"] li',
        '[class*="right-click"] button',
        '[class*="popup-menu"] li',
        '[class*="popup-menu"] button',
    ].join(', ');

    const items = [];
    const seen = new Set();

    document.querySelectorAll(query).forEach(el => {
        if (!isVisible(el)) return;
        const text = (el.innerText || el.textContent || '').trim();
        if (!text) return;
        const key = text.slice(0, 40) + el.tagName;
        if (seen.has(key)) return;
        seen.add(key);
        items.push({
            tag:       el.tagName.toLowerCase(),
            text:      text.slice(0, 60),
            selectors: getSelectorsSimple(el),
            role:      el.getAttribute('role') || '',
            disabled:  el.getAttribute('aria-disabled') === 'true' || el.disabled || false,
        });
    });

    return items;
""")


# ---------------------------------------------------------------------------
# 동적 UI 트리거 감지 JS -- 인터랙션이 있어야 나타나는 요소 대상
# ---------------------------------------------------------------------------
DYNAMIC_TRIGGER_JS = _js("""
    function getBestSelector(el) {
        if (el.id) return '#' + el.id;
        for (const attr of ['data-testid', 'data-test', 'data-cy', 'data-qa']) {
            const v = el.getAttribute(attr);
            if (v) return `[${attr}="${v.replace(/"/g, '\\"')}"]`;
        }
        const aria = el.getAttribute('aria-label');
        if (aria) return `[aria-label="${aria.replace(/"/g, '\\"')}"]`;
        return null;
    }

    const triggers = [];
    const seen = new Set();

    function add(el, action, priority) {
        if (!isVisible(el)) return;
        const sel = getBestSelector(el);
        const key = sel || (el.tagName + '|' + (el.innerText || '').trim().slice(0, 40));
        if (seen.has(key)) return;
        seen.add(key);
        triggers.push({
            selector: sel,
            action,
            priority,
            text: (el.innerText || el.textContent || '').trim().slice(0, 60),
            tag:  el.tagName.toLowerCase(),
        });
    }

    // 1순위: 명시적 팝업/메뉴 트리거
    document.querySelectorAll('[aria-haspopup]').forEach(el => add(el, 'click', 1));

    // 2순위: 접힌 상태 토글
    document.querySelectorAll('[aria-expanded="false"]').forEach(el => add(el, 'click', 2));
    document.querySelectorAll('details:not([open]) > summary').forEach(el => add(el, 'click', 2));

    // 3순위: Bootstrap / 일반 data-toggle
    document.querySelectorAll('[data-toggle],[data-bs-toggle],[data-dropdown]').forEach(el => add(el, 'click', 3));

    // 4순위: aria-controls (패널 컨트롤러)
    document.querySelectorAll('[aria-controls]').forEach(el => add(el, 'click', 4));

    // 5순위: 호버 드롭다운 (nav 하위에 ul 있는 항목)
    document.querySelectorAll('nav li, .nav-item').forEach(el => {
        if (el.querySelector('ul, [role="menu"]')) add(el, 'hover', 5);
    });
    document.querySelectorAll('.dropdown-toggle,[class*="dropdown-trigger"]').forEach(el => add(el, 'hover', 5));

    // 6순위: 툴팁 트리거
    document.querySelectorAll('[data-tooltip],[data-tippy],[data-bs-original-title]').forEach(el => add(el, 'hover', 6));
    document.querySelectorAll('button[title],a[title]').forEach(el => add(el, 'hover', 6));

    return triggers.sort((a, b) => a.priority - b.priority).slice(0, 25);
""")


# ---------------------------------------------------------------------------
# 인터랙션 후 새로 나타난 요소 캡처 JS
# ---------------------------------------------------------------------------
DYNAMIC_CAPTURE_JS = _js("""
    // 팝업/메뉴/드롭다운/툴팁/아코디언에서 나타날 수 있는 요소 패턴
    const query = [
        '[role="menu"] [role="menuitem"]',
        '[role="menu"] li',
        '[role="menubar"] [role="menuitem"]',
        '[role="listbox"] [role="option"]',
        '[role="tooltip"]',
        '[role="dialog"] button, [role="dialog"] a',
        '[role="tree"] [role="treeitem"]',
        '.dropdown-menu li, .dropdown-menu a',
        '.context-menu li, .context-menu a, .context-menu button',
        '[class*="dropdown"] > ul li, [class*="dropdown"] > ul a',
        '[class*="menu__item"], [class*="menu-item"]',
        '[class*="popup"] button, [class*="popup"] a, [class*="popup"] li',
        '[class*="tooltip"]',
        'details[open] > *:not(summary)',
    ].join(', ');

    const items = [];
    const seen = new Set();
    document.querySelectorAll(query).forEach(el => {
        if (!isVisible(el)) return;
        const text = (el.innerText || el.textContent || '').trim();
        if (!text || text.length < 1) return;
        const key = text.slice(0, 40) + el.tagName;
        if (seen.has(key)) return;
        seen.add(key);
        items.push({
            tag:       el.tagName.toLowerCase(),
            text:      text.slice(0, 60),
            selectors: getSelectorsSimple(el),
            role:      el.getAttribute('role') || '',
        });
    });
    return items;
""")


# ---------------------------------------------------------------------------
# 동적 UI 요소 분석 -- 트리거 인터랙션 후 새로 나타난 요소 수집
# ---------------------------------------------------------------------------
async def analyze_dynamic(page) -> list:
    """페이지에서 동적 UI 트리거를 순회하며 인터랙션 후 나타나는 요소를 수집.

    최대 30초 내에 처리 가능한 트리거만 수집한다.
    """
    try:
        triggers = await page.evaluate(DYNAMIC_TRIGGER_JS)
    except Exception as e:
        print(f"     [동적] 트리거 목록 수집 실패 — {e}")
        return []

    origin_url = page.url
    dynamic_elements = []
    deadline = time.monotonic() + 30  # 전체 상한 30초

    for trigger in triggers:
        if time.monotonic() > deadline:
            print("     [동적] 시간 초과 (30초) — 나머지 트리거 건너뜀")
            break

        sel = trigger.get("selector")
        action = trigger.get("action", "click")
        if not sel:
            continue

        try:
            locator = page.locator(sel).first
            if not await locator.is_visible(timeout=1000):
                continue

            if action == "hover":
                await locator.hover(timeout=2000)
            else:
                await locator.click(timeout=2000)

            await page.wait_for_timeout(600)

            # 페이지 이탈 감지 → 복원 실패 시 분석 중단
            if page.url != origin_url:
                try:
                    await page.goto(origin_url, wait_until="networkidle", timeout=15000)
                    await page.wait_for_timeout(300)
                except Exception:
                    print("     [동적] 페이지 복원 실패 — 분석 중단")
                    break
                continue

            revealed = await page.evaluate(DYNAMIC_CAPTURE_JS)

            if revealed:
                dynamic_elements.append({
                    "trigger": {
                        "selector": sel,
                        "action":   action,
                        "text":     trigger.get("text", ""),
                        "tag":      trigger.get("tag", ""),
                    },
                    "revealed": revealed,
                })

        except Exception as e:
            print(f"     [동적] 트리거 실패: {sel} — {e}")
        finally:
            try:
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(200)
            except Exception:
                pass

    return dynamic_elements


# ---------------------------------------------------------------------------
# 우클릭 컨텍스트 메뉴 분석 -- 후보 요소 우클릭 후 메뉴 캡처
# ---------------------------------------------------------------------------
async def analyze_contextmenu(page) -> list:
    """CONTEXTMENU_CANDIDATES를 순회하며 우클릭 후 나타나는 메뉴 항목을 수집.

    타입별 첫 번째 visible 요소만 시도하고, 동일 메뉴 내용은 중복 제외.
    최대 30초 내에 처리 가능한 후보만 수집한다.
    """
    origin_url = page.url
    results = []
    seen_menu_sigs = set()
    deadline = time.monotonic() + 30  # 전체 상한 30초

    for candidate_sel in CONTEXTMENU_CANDIDATES:
        if time.monotonic() > deadline:
            print("     [우클릭] 시간 초과 (30초) — 나머지 후보 건너뜀")
            break

        try:
            locator = page.locator(candidate_sel).first
            if not await locator.is_visible(timeout=500):
                continue

            # 트리거 요소의 베스트 셀렉터 추출
            trigger_sel = await locator.evaluate("""el => {
                if (el.id) return '#' + el.id;
                for (const a of ['data-testid','data-test','data-cy','data-qa']) {
                    const v = el.getAttribute(a);
                    if (v) return `[${a}="${v.replace(/"/g,'\\\\"')}"]`;
                }
                const aria = el.getAttribute('aria-label');
                if (aria) return `[aria-label="${aria.replace(/"/g,'\\\\"')}"]`;
                return null;
            }""")
            trigger_text = (await locator.evaluate(
                "el => (el.innerText || el.textContent || '').trim().slice(0, 60)"
            ))
            trigger_tag = await locator.evaluate("el => el.tagName.toLowerCase()")

            # 우클릭
            await locator.click(button="right", timeout=2000)
            await page.wait_for_timeout(600)

            # 페이지 이탈 감지 → 복원 실패 시 분석 중단
            if page.url != origin_url:
                try:
                    await page.goto(origin_url, wait_until="networkidle", timeout=15000)
                    await page.wait_for_timeout(300)
                except Exception:
                    print("     [우클릭] 페이지 복원 실패 — 분석 중단")
                    break
                continue

            menu_items = await page.evaluate(CONTEXTMENU_CAPTURE_JS)

            if not menu_items:
                continue

            # 메뉴 내용 시그니처로 중복 제거
            sig = "|".join(item["text"] for item in menu_items[:6])
            if sig in seen_menu_sigs:
                continue
            seen_menu_sigs.add(sig)

            results.append({
                "trigger": {
                    "selector": trigger_sel or candidate_sel,
                    "action":   "rightclick",
                    "text":     trigger_text,
                    "tag":      trigger_tag,
                },
                "revealed": menu_items,
            })

        except Exception as e:
            print(f"     [우클릭] 후보 실패: {candidate_sel} — {e}")
        finally:
            try:
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(200)
            except Exception:
                pass

    return results


# ---------------------------------------------------------------------------
# 단일 async 진입점 -- 브라우저 1회만 생성
# ---------------------------------------------------------------------------
async def analyze_all(main_url: str, sub_urls: list[str],
                      force_refresh: bool = False,
                      skip_dynamic: bool = False) -> tuple[dict, dict]:
    """메인 URL + 서브 URL을 단일 브라우저에서 분석.

    Returns: (main_dom, {sub_url: sub_dom, ...})
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # ── 메인 URL: networkidle (품질 우선) ──
        main_dom = None
        if not force_refresh:
            main_dom = get_cached_dom(main_url)
            if main_dom:
                print(f"[01] 캐시 사용: {main_url}")

        # 캐시 히트 + 동적 요소 만료 → 동적 분석만 재실행
        needs_dynamic = (
            main_dom is not None
            and not skip_dynamic
            and "dynamic_elements" not in main_dom
            and "contextmenu_elements" not in main_dom
        )
        if needs_dynamic:
            print("[01] 동적 캐시 만료 — 동적 분석만 재실행")

        if main_dom is None or needs_dynamic:
            page = await browser.new_page()
            try:
                await page.goto(main_url, wait_until="networkidle", timeout=30000)
                if main_dom is None:
                    main_dom = await page.evaluate(DOM_EXTRACT_JS)

                # 동적 UI 분석: 같은 페이지 세션에서 트리거 순회
                if not skip_dynamic:
                    print("[01] 동적 UI 요소 분석 중 (hover·click 트리거)...")
                    dynamic = await analyze_dynamic(page)
                    if dynamic:
                        main_dom["dynamic_elements"] = dynamic
                        print(f"     동적 트리거 {len(dynamic)}개 → 노출 요소 수집 완료")
                    else:
                        print("     동적 트리거 없음 (정적 페이지)")

                    print("[01] 우클릭 컨텍스트 메뉴 분석 중...")
                    contextmenu = await analyze_contextmenu(page)
                    if contextmenu:
                        main_dom["contextmenu_elements"] = contextmenu
                        print(f"     우클릭 메뉴 {len(contextmenu)}종 캡처 완료")
                    else:
                        print("     우클릭 메뉴 없음")

                save_dom_cache(main_url, main_dom)
            except Exception as e:
                return {"error": str(e), "url": main_url}, {}
            finally:
                await page.close()

        # ── 서브 URL: load + 500ms (속도 우선) ──
        sub_doms = {}
        uncached = []
        for url in sub_urls:
            if not force_refresh:
                cached = get_cached_dom(url)
                if cached:
                    print(f"[01] 서브페이지 캐시 사용: {url}")
                    sub_doms[url] = cached
                    continue
            uncached.append(url)

        if uncached:
            print(f"[01] 서브페이지 {len(uncached)}개 병렬 분석 중...")
            semaphore = asyncio.Semaphore(8)

            async def _analyze_sub(url):
                async with semaphore:
                    page = await browser.new_page()
                    try:
                        await page.goto(url, wait_until="load", timeout=15000)
                        await page.wait_for_timeout(500)
                        dom = await page.evaluate(DOM_EXTRACT_JS)
                        save_dom_cache(url, dom)
                        return (url, dom)
                    except Exception as e:
                        print(f"     경고: {url} 접근 실패 -- {e}")
                        return (url, None)
                    finally:
                        await page.close()

            results = await asyncio.gather(*[_analyze_sub(u) for u in uncached])
            for _url, _dom in results:
                if _dom is not None:
                    sub_doms[_url] = _dom

        await browser.close()
        return main_dom, sub_doms



def extract_subpage_urls(test_cases: list, base_url: str) -> list:
    """테스트 케이스의 precondition과 steps에서 고유 서브페이지 URL을 추출."""
    urls = set()
    for tc in test_cases:
        # precondition에서 URL 추출
        precondition = tc.get("precondition", "")
        found = re.findall(r'https?://[^\s,)>\]"]+', precondition)
        for u in found:
            u = u.rstrip(".,;:")
            if u != base_url and u.rstrip("/") != base_url.rstrip("/"):
                urls.add(u)

        # steps 리스트에서 URL 추출
        steps = tc.get("steps", [])
        if isinstance(steps, list):
            for step in steps:
                step_text = step if isinstance(step, str) else str(step)
                found = re.findall(r'https?://[^\s,)>\]"]+', step_text)
                for u in found:
                    u = u.rstrip(".,;:")
                    if u != base_url and u.rstrip("/") != base_url.rstrip("/"):
                        urls.add(u)

    return sorted(urls)


def _make_analyze_mutator(dom: dict, url: str, sub_doms):
    """분석 결과 필드만 최신 상태 위에 병합하는 mutator를 만든다.

    analyze_all()은 메인+서브 페이지를 브라우저로 순회하므로 수 분이 걸릴 수 있다.
    그 사이 대시보드 등 다른 프로세스가 pipeline.json을 갱신하면, 미리 읽어둔 state를
    통째로 되쓸 때 그 변경이 유실된다. 이 스크립트가 소유한 필드만 갱신한다.
    """
    def _mutator(fresh: dict) -> dict:
        # dom_info는 다운스트림(02a_dialog, 06a_dialog 등)이 직접 참조 — 인라인 저장 필수
        # dom_cache_key는 캐시 파일 참조용 (서브페이지는 sub_dom_keys로 캐시 키만 저장)
        updated = {
            **fresh,
            "dom_info": dom,
            "dom_cache_key": url_cache_key(url),
            "step": Step.ANALYZED,  # P68: 리터럴 → 상수
        }
        if sub_doms:
            # pipeline.json에는 URL→캐시키 매핑만 저장 (경량화)
            updated["sub_dom_keys"] = {
                sub_url: url_cache_key(sub_url) for sub_url in sub_doms
            }
        return updated

    return _mutator


def main():
    state_path = PIPELINE_STATE
    if not state_path.exists():
        print("[오류] state/pipeline.json 없음. 먼저 run_qa.py를 실행하세요.")
        sys.exit(1)

    force_refresh  = "--force-refresh"  in sys.argv
    skip_dynamic   = "--skip-dynamic"   in sys.argv

    state = read_state(state_path)
    url = state["url"]

    print(f"[01] 페이지 분석 중: {url}")
    if skip_dynamic:
        print("[01] --skip-dynamic: 동적 UI 분석 건너뜀")

    # 서브페이지 URL 추출
    test_cases = state.get("test_cases", [])
    sub_urls = extract_subpage_urls(test_cases, url)

    # 단일 브라우저로 메인 + 서브 모두 분석
    dom, sub_doms = asyncio.run(analyze_all(url, sub_urls, force_refresh, skip_dynamic))

    if "error" in dom:
        print(f"[오류] 페이지 접근 실패: {dom['error']}")
        sys.exit(1)

    update_state(state_path, _make_analyze_mutator(dom, url, sub_doms))

    if sub_doms:
        print(f"[01] 서브페이지 {len(sub_doms)}개 분석 완료")

    visible_inputs  = [i for i in dom.get('inputs',  []) if i.get('visible')]
    hidden_inputs   = [i for i in dom.get('inputs',  []) if not i.get('visible')]
    visible_buttons = [b for b in dom.get('buttons', []) if b.get('visible')]
    hidden_buttons  = [b for b in dom.get('buttons', []) if not b.get('visible')]

    dynamic = dom.get("dynamic_elements", [])
    contextmenu = dom.get("contextmenu_elements", [])
    total_revealed = sum(len(d.get("revealed", [])) for d in dynamic)
    total_cm_items = sum(len(d.get("revealed", [])) for d in contextmenu)

    print(f"[01] 완료 ─ 제목: {dom.get('title','')}")
    print(f"       입력 필드:    {len(visible_inputs)}개 (hidden {len(hidden_inputs)}개 포함)")
    print(f"       버튼:         {len(visible_buttons)}개 (hidden {len(hidden_buttons)}개 포함)")
    print(f"       숨겨진 UI:    {len(dom.get('hidden_elements', []))}개 (모달·메뉴 등)")
    print(f"       네비게이션:   {len(dom.get('navItems', []))}개 (사이드바·메뉴 li)")
    print(f"       에러 영역:    {len(dom.get('errors', []))}개")
    print(f"       컴포넌트:     {len(dom.get('components', []))}개")
    print(f"       ID 요소:      {len(dom.get('idElements', []))}개")
    print(f"       testid:       {len(dom.get('testidElements', []))}개")
    print(f"       동적 트리거:  {len(dynamic)}개 → 노출 요소 {total_revealed}개")
    if dynamic:
        for d in dynamic[:3]:
            t = d['trigger']
            print(f"         [{t['action']}] {t['text'][:30]} → {len(d['revealed'])}개 항목")
    print(f"       우클릭 메뉴:  {len(contextmenu)}종 → 메뉴 항목 {total_cm_items}개")
    if contextmenu:
        for d in contextmenu[:3]:
            t = d['trigger']
            items_preview = ", ".join(i['text'] for i in d['revealed'][:3])
            print(f"         [{t['tag']}] {t['text'][:20]} → {items_preview[:50]}")
    print()
    print("[다음] Claude Code가 dom_info를 읽고 테스트 전략(plan)을 수립합니다.")


if __name__ == "__main__":
    main()
