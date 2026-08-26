// ── Constants ──
var ROLE_LABEL = { senior: '사수', junior: '부사수', deliberation: '심의' };
var ROLE_CLASS = { senior: 'role-senior', junior: 'role-junior', deliberation: 'role-deliberation' };
var BUBBLE_CLASS = { senior: 'bubble-senior', junior: 'bubble-junior', deliberation: 'bubble-deliberation' };
var STATUS_LABEL = {
  in_progress: '진행 중', discussed: '결론 도출', approved: '승인됨',
  revision_needed: '수정 요청', rejected: '반려됨',
};
var STATUS_CLASS = {
  in_progress: 'status-in_progress', discussed: 'status-in_progress',
  approved: 'status-approved', revision_needed: 'status-revision_needed', rejected: 'status-revision_needed',
};
var MSG_STATUS_STYLE = {
  approved: 'background:#1a2e1e;color:#3fb950;border:1px solid #238636',
  revision_needed: 'background:#2d1212;color:#f85149;border:1px solid #da3633',
};

// ── 파이프라인 단계 상수 (초기 fallback; /api/pipeline_registry fetch 후 갱신) ──
// P45: 이 값들은 _pipeline_registry.py에서 동적으로 로드된다.
//      fetch 완료 전 또는 실패 시 아래 하드코딩 fallback을 사용한다.
var PIPELINE_STEPS = ['init', 'analyzed', 'planned', 'generated', 'reviewed', 'done'];
var STEP_LABELS = {
  init: 'Init', analyzed: '분석', planned: '계획', generated: '생성',
  reviewed: '리뷰', done: '완료', heal_needed: '힐링필요', heal_failed: '힐링실패',
  scaffolded: '생성', linted: '생성', approved: '리뷰',
};
// 구 step 값 → 현재 step 값 호환 맵 (pipeline.js STEP_COMPAT 전역 노출, P45)
var STEP_COMPAT = { scaffolded: 'generated', linted: 'generated', approved: 'reviewed' };

var PARALLEL_STEPS = ['init', 'analyzing', 'ready', 'generating', 'testing', 'done'];
var PARALLEL_STEP_LABELS = {
  init: '초기화', analyzing: 'DOM 분석', ready: '코드 생성 대기',
  generating: '코드 생성', testing: '테스트 실행', done: '완료',
  heal_needed: '힐링필요', heal_failed: '힐링실패',
};

var TESTS_PER_PAGE = 20;
var REPORTS_PER_PAGE = 20;

// ── 레지스트리 동기화 (P45) ──────────────────────────────────────────────────
// /api/pipeline_registry (백엔드 _pipeline_registry.py 기반)에서 상수를 fetch해
// 위 전역 변수를 갱신한다. 성공하면 다음 렌더 사이클부터 최신 값이 반영된다.
// fetch 완료 전 또는 오류 시 위 fallback 하드코딩값이 유지된다.
(function initRegistryConstants() {
  fetch('/api/pipeline_registry')
    .then(function(r) { return r.ok ? r.json() : null; })
    .then(function(data) {
      if (!data) return;
      var p = data.pipeline;
      if (p) {
        if (p.steps)       PIPELINE_STEPS = p.steps;
        if (p.step_labels) STEP_LABELS    = p.step_labels;
        if (p.step_compat) STEP_COMPAT    = p.step_compat;
      }
      var q = data.parallel;
      if (q) {
        if (q.steps)       PARALLEL_STEPS       = q.steps;
        if (q.step_labels) PARALLEL_STEP_LABELS = q.step_labels;
      }
    })
    .catch(function() { /* 네트워크 오류 — fallback 유지 */ });
}());
