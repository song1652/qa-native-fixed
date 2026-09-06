// ── Global State (let → var for cross-file scope) ──
var lastJson = '';
var refreshCount = 0;
var collapsedSessions = {};
var currentView = '';
var lastData = null;
var pipelineState = null;
var batchState = null;
var reportsList = [];
var pagesData = { pages: {}, groups: [] };
var generatedGroups = [];
var quickState = {};

// UI 상태 보존 (리프레시 시 유지)
var _uiState = {
  openReportName: null,         // 리포트 뷰: 열린 리포트 이름
  parallelReportName: null,     // 병렬 뷰: 열린 리포트 이름
  singleReportName: null,       // 단일 뷰: 열린 리포트 이름
  mergeLogVisible: false,       // 병렬 뷰: merge 로그 표시 여부
  mergeLogContent: '',          // 병렬 뷰: merge 로그 내용
  scrollTop: {},                // 뷰별 스크롤 위치
  overviewLogTab: 'run_qa.txt', // Overview: 선택된 로그 탭
};

// 데이터 변경 감지용 이전 상태 해시
var _prevPipelineJson = '';
var _prevBatchJson = '';
var _prevReportsJson = '';

// Dashboard Overview 데이터 캐시
var _ovRunHistory = null;
var _ovHealStats = null;
var _ovFlakyTests = null;
var _ovDataLoaded = false;
var _ovLogAutoRefresh = null;  // 로그 자동 갱신 타이머 (전역 보관, orphan 방지)

// Group Result: 접기/펼치기 공통
var _groupOpenState = {};

// Test List 상태
var _testListState = {};

// Test Detail 열림 상태 & 콘텐츠 캐시 (nodeid → bool / string)
var _testDetailOpen = {};
var _testDetailContent = {};

// 로그 타이머
var _logTimers = {};

// Quick Run 상태
var _quickRunState = { running: false, logVisible: false, logContent: '' };

// Reports 상태
var _reportListState = { search: '', sort: 'newest', page: 1, selected: new Set(), busy: false };
var _reportFetchVersion = 0;
