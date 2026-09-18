// Import Studio — 공유 상태 + 상수
// 프로젝트 관례상 ES 모듈을 쓰지 않으므로(대시보드 전체가 plain <script> +
// 전역 공유 방식), IIFE + 공유 네임스페이스 객체(window.__importStudioNS)로
// 파일 간 경계를 나눈다. 로드 순서: state → utils → api → render → handlers → main.
(function (NS) {
  'use strict';

  const state = {
    step: 1,              // 현재 단계 (1~5)
    files: [],            // GET /api/import/files 결과
    selectedSources: [],  // [{ fileId, sheets: [] }] — 한 번의 run으로 묶을 원본
    mappings: {},         // 모든 원본에 적용되는 공통 매핑
    sourceMappings: {},   // { "fileId::sheet": { tc_id: "A열" } } 예외 매핑
    activeMappingSource: '',
    profiles: [],         // GET /api/import/profiles 결과
    previewResult: null,  // POST /api/import/preview 결과 (모든 시트 합산)
    runId: null,          // preview/commit/result/rollback을 잇는 단일 작업 ID
    idempotencyKey: null, // 같은 run의 중복 커밋을 안전하게 재조정하기 위한 키
    commitResult: null,   // POST /api/import/commit 결과
    rollbackResult: null, // 롤백 후에도 완료 화면에서 최종 상태를 보존
    decisions: {},        // { rowKey: 'exclude' } — 충돌 행은 명시적 결정 필수
    modal: null,          // 앱 내부 입력/확인 대화상자
    loading: false,       // 전역 로딩 상태
    error: null,          // 에러 메시지
    policy: 'skip-conflict', // Step4 정책 선택
    activeFilter: 'all',     // Step3 필터
  };

  // 단계별 유효성 검사 규칙
  // Step3: 충돌 미처리도 통과 — 충돌은 Step4 정책(skip-conflict/overwrite)으로 일괄 처리
  const validators = {
    1: (s) => s.selectedSources.length > 0 && s.selectedSources.every((source) => source.sheets.length > 0),
    2: (s) => ['tc_id', 'title', 'precondition', 'steps', 'expected'].every((f) => s.mappings[f]),
    3: (s) => s.previewResult !== null,
    4: (s) => s.commitResult !== null && s.commitResult.status === 'committed',
  };

  // TC 필드 정의 (Step2 매핑)
  const TC_FIELDS = [
    { key: 'tc_id',         label: 'TC ID',      required: true },
    { key: 'title',         label: '제목',        required: true },
    { key: 'precondition',  label: '사전 조건',   required: true },
    { key: 'steps',         label: '테스트 단계', required: true },
    { key: 'expected',      label: '예상 결과',   required: true },
    { key: 'priority',      label: '우선순위',    required: false },
    { key: 'tags',          label: '태그',        required: false },
    { key: 'group',         label: '그룹',        required: false },
  ];

  // 기본 QA-Native Excel 템플릿의 열 순서. 2단계 진입 시 한 번만
  // 적용하고, 사용자가 수정한 매핑은 이후 렌더링에서도 보존한다.
  const DEFAULT_MAPPINGS = {
    tc_id: 'B열',
    title: 'F열',
    precondition: 'G열',
    steps: 'H열',
    expected: 'I열',
  };

  Object.assign(NS, { state, validators, TC_FIELDS, DEFAULT_MAPPINGS });
})(window.__importStudioNS = window.__importStudioNS || {});
