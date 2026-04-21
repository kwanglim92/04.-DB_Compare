# Server Spec Manager 기능 강화 맥락 노트

## 결정 기록

| 결정 사항 | 선택지 | 최종 선택 | 이유 |
|-----------|--------|-----------|------|
| 통합 방향 | A: SSM에 PM 흡수 / B: PM을 데이터소스 전환형 / C: 역할 분리 | A | 사용자 선택. SSM에 모든 기능 집중, PM은 오프라인 전용 유지 |
| Add/Edit 다이얼로그 | 2개 유지 vs 1개 통합 | 1개 통합 (SpecItemDialog) | 코드 중복 제거, UI 일관성 |
| 트리뷰 패턴 | 새로 작성 vs PM 패턴 참조 | PM 패턴 참조 (display_as_tree) | 이미 검증된 코드, 동일한 데이터 구조 |

## 참조 자료
- `src/ui/profile_manager.py` — 트리뷰, 검색 하이라이트, Import/Export, 우클릭 메뉴 패턴
- `src/ui/spec_item_editor.py` — 기존 편집 다이얼로그 (스크롤, 레이아웃 참조)
- `src/core/server_db_manager.py` — 서버 CRUD 레이어 (프로필 CRUD 메서드 추가 필요)
- `src/utils/format_helpers.py` — format_spec(), center_window_on_parent() 재사용

## 제약 조건
- 기존 Profile Manager는 그대로 유지 (오프라인 모드용)
- Server Spec Manager는 온라인 모드에서만 사용
- 서버 DB 스키마 변경 없음 (기존 테이블 구조 활용)
- bump_version()은 모든 쓰기 연산에서 자동 호출

## 사용자 요구사항 원문
> 옵션 1로 진행 하고 싶어 원하는 기능들을 전부 구현했기 때문에 유용하게 사용할 수 있을것 같아.
> server DB 에서 항목 추가 팝업창 UI 최적화 해줘.
> Profile Manager 기능을 Server Spec Manager에 흡수 — 트리뷰, Import/Export, 프로필 CRUD, 검색 하이라이트, 우클릭 메뉴 추가.
