# PLAN: 사용성 강화 (v1.4.0) — 검색 / 임포트 / 결과 필터

## 목표
- 일상 워크플로우의 클릭 수와 인지 부하 감소
- 신규 프로필 작성 시 자료구조 일관성 확보
- PRD §11 "장비당 QC ≤15분" 목표 달성에 기여

## 범위

### F1. DB STRUCTURE 검색
- **변경 파일**: `src/ui/tree_view.py`, `src/ui/main_window.py`
- **핵심**: `DBTreeView._build_search_index()` + `search()` / `clear_search()` + 메인창 검색 입력창(250ms 디바운스)
- **동작**: 매칭 시 자동 expand + 노란 하이라이트 + 첫 매치 스크롤. 클리어 시 expand 상태 복원.
- **신규 태그**: `search_hit` (#fff59d 배경)

### F2. Admin Spec 관리 모듈 일괄 임포트
- **변경 파일**: `src/ui/server_spec_manager.py`, `src/core/server_db_manager.py`
- **신규 클래스**: `ModuleImportDialog` (CTkToplevel, 모달)
  - Step 1: 소스 라디오 (DB 폴더 / Common Base / 다른 Profile)
  - Step 2: 트리 + 체크박스 + gold 중복 표시 + 검색
  - Step 3: 충돌 라디오 (Skip 기본 / Update / Abort) + 임포트 실행
- **신규 메서드**: `ServerDBManager.bulk_add_specs(profile_id, items, conflict_strategy)`
  - 단일 트랜잭션, `bump_version` 1회만 호출
  - `profile_id=None` ⇒ Common Base, int ⇒ profile additional_checks
- **read_only**: "+ 임포트" 버튼을 `_edit_buttons`에 등록 → 오프라인 시 자동 비활성

### F3. Profile Viewer 결과 필터
- **변경 파일**: `src/ui/main_window.py`
- **UI**: `viewer_header`에 `CTkSegmentedButton` `[ All | Pass | Check | Fail ]`
- **상태**: `viewer_filter`, `_all_viewer_rows`, `_viewer_counts`
- **메서드**: `set_viewer_filter()`, `_apply_viewer_filter()`, `_recount_viewer()`, `_update_viewer_count_label()`
- **동작**: 클리어/재삽입 패턴, 카운트 라벨 동시 갱신, 프로필 변경 시 자동 리셋

## 설계 원칙
- 기존 `update_profile_viewer_with_results`, `load_profile_to_viewer`, `DBTreeView.populate` 시그니처 불변
- `equipment_profiles` 데이터 구조 불변 (bulk_add_specs는 동일 형식으로 INSERT/UPDATE만)
- 회귀 테스트 (66개) 100% 통과

## 검증
1. `python -m pytest tests/ -q` → 66/66 통과
2. `python -m py_compile` → 전체 성공
3. 핵심 import 검증
4. 수동: F1/F2/F3 시나리오별 동작 확인

## 리스크
| 리스크 | 대응 |
|--------|------|
| 대용량 DB(2,600+) 검색 지연 | 인덱스 1회 구축 + 250ms 디바운스 |
| ttk.Treeview 다중 태그 표시 우선순위 | 검색 시 원본 태그 보관 + search_hit 단일 태그로 교체, 클리어 시 원본 복원 |
| bulk_add_specs 부분 실패 | 단일 트랜잭션으로 보장, abort 시 ROLLBACK |
| F3 필터 + DB 트리 동기화 | 상호 독립 (DB 트리는 별도 DBTreeView, Profile Viewer는 별도 ttk.Treeview) |
