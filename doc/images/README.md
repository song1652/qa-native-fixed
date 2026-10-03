# 현재 제품 화면과 촬영 기준

- 촬영 날짜: 대시보드 **2026-10-03**, TC 스튜디오 **2026-10-02**.
- 기준 구현: 밝은 테마 및 1·2·3차 안정화 적용 작업본.
- 서버: 대시보드 캡처는 저장소를 복제한 실제 `serve.py` **http://localhost:62916/**, TC 스튜디오는 **http://localhost:8766/**.
- 도구: Playwright Chromium. 화면 크기 **1440 × 1000**, 개요와 작성 규칙 편집은 전체 항목을 보여 주기 위해 **1440 × 1400**을 사용했습니다.
- 스위트 이름·건수·시각은 촬영 당시 예시 환경의 값이며 사용자 환경에서는 달라집니다.

## 대시보드

`dashboard-user-guide/`는 검증용 복제 저장소에서 실제 Playwright 테스트를 실행한 화면입니다. 가상 회원 등록 화면의 성공·의도된 실패·복구 검증 실패·서버 재시작·취소·실행 파일 없는 실패를 기록했습니다. 리포트는 실제 생성 결과를 열었습니다. API 응답을 가짜로 주입하지 않았으며 사용자 원본의 실행 데이터는 변경하지 않았습니다.

| 이미지 | 화면 |
|---|---|
| [01-overview.png](dashboard-user-guide/01-overview.png) | 대시보드와 통과·주의·실패 범례 |
| [02-quick-run.png](dashboard-user-guide/02-quick-run.png) | 빠른 실행 |
| [03-single-pipeline.png](dashboard-user-guide/03-single-pipeline.png) | 단일 파이프라인 |
| [04-parallel-pipeline.png](dashboard-user-guide/04-parallel-pipeline.png) | 병렬 파이프라인 |
| [05-reports.png](dashboard-user-guide/05-reports.png) | 리포트 목록 |
| [06-history.png](dashboard-user-guide/06-history.png) | 실행 기록 |
| [07-team.png](dashboard-user-guide/07-team.png) | 새 토론 시작 |
| [08-pages.png](dashboard-user-guide/08-pages.png) | 페이지 URL 관리 |
| [09-report-open.png](dashboard-user-guide/09-report-open.png) | 실제 저장된 리포트 열기 |
| [10-report-detail.png](dashboard-user-guide/10-report-detail.png) | 그룹과 TC 상세 펼치기 |
| [11-recovery-notices.png](dashboard-user-guide/11-recovery-notices.png) | 오류 원인과 대응·브라우저별 확인 |
| [12-execution-stopped.png](dashboard-user-guide/12-execution-stopped.png) | 중단 및 리포트 없는 실패 기록 |

## TC 스튜디오

`tc-studio-user-guide/`는 실제 제품의 현재 UI입니다. 파일 가져오기와 Markdown 내보내기는 **미리보기까지만** 진행했습니다. 이름 변경·프로필 저장·스위트 삭제·복원·md 반영을 실행하지 않았습니다.

**초안 검토 `03-review.png`만 브라우저에 예시 응답을 넣어 촬영했습니다.** 서버 TC의 상태는 바꾸지 않았으며 이 이미지는 실제 LLM 생성 성공의 증거가 아닙니다. 나머지는 조회한 화면과 실제 입력 파일의 분석 결과입니다. 휴지통은 촬영 당시 빈 상태입니다.

| 이미지 | 화면 |
|---|---|
| [01-planning.png](tc-studio-user-guide/01-planning.png) | 기획 입력과 작성 위치 |
| [02-library.png](tc-studio-user-guide/02-library.png) | TC 라이브러리 |
| [03-review.png](tc-studio-user-guide/03-review.png) | 초안 검토 — 브라우저 예시 응답 |
| [04-export.png](tc-studio-user-guide/04-export.png) | Excel·Markdown 내보내기 |
| [05-import.png](tc-studio-user-guide/05-import.png) | Excel 열 매핑과 미리보기 |
| [06-import-history.png](tc-studio-user-guide/06-import-history.png) | 가져오기 이력 |
| [07-suite-delete.png](tc-studio-user-guide/07-suite-delete.png) | 스위트 삭제 확인 — 취소 |
| [08-sheet-rename.png](tc-studio-user-guide/08-sheet-rename.png) | 시트 이름 변경 — 취소 |
| [09-writing-profile.png](tc-studio-user-guide/09-writing-profile.png) | 작성 규칙 편집 — 저장하지 않음 |
| [10-case-detail.png](tc-studio-user-guide/10-case-detail.png) | TC 상세 편집 — 조회 |
| [11-suite-trash.png](tc-studio-user-guide/11-suite-trash.png) | 삭제한 스위트 — 빈 목록 |
| [12-md-preview.png](tc-studio-user-guide/12-md-preview.png) | Markdown 변경 미리보기 — 반영하지 않음 |

화면 변경 시 영향을 받는 이미지를 다시 촬영하고 날짜·기준 구현·예시 응답 여부를 함께 갱신합니다. 개인정보·연결 토큰·비공개 기획이 포함된 화면은 공유 이미지로 저장하지 않습니다.
