# CHECKLIST: 사용성 강화 v1.4.0

## Phase A — F3: Profile Viewer 결과 필터
- [x] A.1 `_all_viewer_rows`, `viewer_filter`, `_viewer_counts` 인스턴스 변수 초기화
- [x] A.2 `viewer_header`에 SegmentedButton 추가
- [x] A.3 `load_profile_to_viewer` / `update_profile_viewer_with_results` 끝에서 캐시 빌드
- [x] A.4 `_apply_viewer_filter()`, `_recount_viewer()`, `_update_viewer_count_label()`, `set_viewer_filter()` 구현
- [x] A.5 프로필 변경 시 필터 자동 리셋
- [x] A.6 QC 미실행 상태에서 안내 (`update_status` 호출)
- [x] A.7 필터 전환 시 선택 항목 보존

## Phase B — F1: DB STRUCTURE 검색
- [x] B.1 `DBTreeView._build_search_index()` (populate 끝에서 자동 호출)
- [x] B.2 `tree.tag_configure('search_hit', ...)` 추가 (노랑 배경)
- [x] B.3 `DBTreeView.search()` / `clear_search()` / `_clear_highlights_only()` / `has_data()` 구현
- [x] B.4 expand 상태 보존 (`_saved_open_state`) + 클리어 시 복원
- [x] B.5 `main_window.py`에 검색 입력창 + 디바운스(250ms) + 카운트 라벨
- [x] B.6 `display_db_tree` 호출 시 검색 입력 활성화
- [x] B.7 ESC로 검색 클리어, Enter로 즉시 실행

## Phase C — F2: 모듈 일괄 임포트
- [x] C.1 `ServerDBManager.bulk_add_specs(profile_id, items, conflict_strategy)` 구현 (단일 트랜잭션)
- [x] C.2 `ModuleImportDialog` 신규 클래스 (`server_spec_manager.py`)
- [x] C.3 Step 1: 소스 라디오 (DB 폴더 / Common Base / 다른 Profile)
- [x] C.4 Step 2: 트리 + 체크박스 (☑/☐) + gold 중복 표시 + 검색 필터
- [x] C.5 Step 3: 충돌 라디오 (Skip / Update / Abort) + 카운트 요약
- [x] C.6 "+ 임포트" 버튼 추가 (`_create_tab` 툴바, `_edit_buttons`에 등록)
- [x] C.7 read_only 모드 자동 비활성
- [x] C.8 임포트 후 `_load_tab_data` + `_notify_change` 호출 (UI/캐시 동기화)

## Phase D — 문서 / 릴리즈
- [x] D.1 `docs/CHANGELOG.md` v1.4.0 섹션 추가
- [x] D.2 메인 창 타이틀 v1.3.0 → v1.4.0
- [x] D.3 `.cwm/docs/plans/260421-usability-search-import-filter/` 플랜 폴더 생성
- [ ] D.4 `docs/PRD_DB_Manager_v1.1.0.md` §8.3 (Nice-to-Have) → §8.1 (Must-Have) 이동 (선택사항)

## Phase E — 검증
- [x] E.1 `python -m py_compile` 전체 성공
- [x] E.2 핵심 import 검증 (`MainWindow`, `ServerSpecManagerPanel`, `ModuleImportDialog`, `bulk_add_specs`, `DBTreeView.search`, `DBTreeView.has_data`)
- [x] E.3 기존 66개 테스트 회귀 통과
- [ ] E.4 수동 검증 — F1 (DB 검색 + expand/클리어/0매치/한글)
- [ ] E.5 수동 검증 — F2 (3가지 소스 / 3가지 충돌 전략 / read_only 비활성)
- [ ] E.6 수동 검증 — F3 (필터 전환 / 카운트 / 프로필 변경 리셋 / QC 미실행 안내)
- [ ] E.7 EXE 빌드 테스트
