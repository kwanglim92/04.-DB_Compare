# Server Spec Manager 기능 강화 계획서

## 개요
- **목적**: Server Spec Manager에 Profile Manager의 핵심 기능을 흡수하여, 서버 DB를 직관적으로 관리할 수 있는 완성된 도구로 만든다
- **범위**: `src/ui/server_spec_manager.py`, `src/core/server_db_manager.py`, Add/Edit 다이얼로그
- **예상 단계**: 5 Phase

## 현재 상태 분석

### Server Spec Manager (현재)
- 탭 기반 프로필 전환 (Common Base + 장비별)
- 테이블 뷰 1가지 (headings 모드)
- 기본 CRUD (추가/편집/삭제)
- 검색 (필터링만, 하이라이트 없음)
- 컬럼 정렬
- Add/Edit 팝업 — 기능은 동작하지만 UI 레이아웃 최적화 필요

### Profile Manager에서 흡수할 기능
1. **트리 뷰 모드** — Module > PartType > Part > Item 계층구조 (테이블/트리 토글)
2. **검색 하이라이트** — 매칭 항목 오렌지색 하이라이트
3. **우클릭 컨텍스트 메뉴** — 편집/삭제 빠른 접근
4. **프로필 CRUD** — 프로필 생성/이름변경/삭제 (서버 DB에서)
5. **Import/Export** — JSON 파일로 프로필 내보내기/가져오기 (서버 DB ↔ JSON)
6. **Add Item 팝업 최적화** — 컴팩트 레이아웃, 타입별 필드 전환 개선

## 구현 계획

### Phase 1: Add/Edit 다이얼로그 UI 최적화
- `AddSpecItemDialog` / `EditSpecItemDialog` 통합 → `SpecItemDialog` 하나로
- 컴팩트 그리드 레이아웃 (420x400 이하)
- validation_type 변경 시 필드 즉시 전환
- 타입별 불필요한 필드 숨김 (range: Min/Max만, exact: Expected만, check: 없음)
- **변경 파일**: `src/ui/server_spec_manager.py`

### Phase 2: 트리 뷰 모드 추가
- 테이블/트리 뷰 토글 스위치 추가
- 트리 뷰: Module > PartType > PartName > Item 계층구조
- 아이콘 표시 (📁 Module, 📂 PartType, 📄 Part, • Item)
- 항목 수 카운트 표시 (각 노드 옆)
- Treeview 컬럼 동적 재구성 (테이블 8열 ↔ 트리 3열)
- **변경 파일**: `src/ui/server_spec_manager.py`

### Phase 3: 검색 강화 + 우클릭 메뉴
- 검색 하이라이트: 매칭 항목에 `search_match` 태그 (오렌지 배경)
- 우클릭 컨텍스트 메뉴: 편집 / 삭제 / 항목 경로 복사
- 다중 선택 지원 (Ctrl+Click, Shift+Click)
- **변경 파일**: `src/ui/server_spec_manager.py`

### Phase 4: 프로필 CRUD (서버 DB)
- 프로필 생성: 새 탭 추가 + DB INSERT
- 프로필 이름 변경: 탭명 변경 + DB UPDATE
- 프로필 삭제: 탭 제거 + DB DELETE (CASCADE)
- `ServerDBManager`에 프로필 CRUD 메서드 추가
- 탭 우클릭 메뉴로 접근 (Rename/Delete)
- **변경 파일**: `src/core/server_db_manager.py`, `src/ui/server_spec_manager.py`

### Phase 5: Import/Export (서버 DB ↔ JSON)
- Export: 현재 탭의 데이터를 JSON 파일로 내보내기 (프로필 구조 유지)
- Import: JSON 파일에서 프로필 데이터를 서버 DB로 가져오기
- 기존 Profile Manager의 export 포맷과 호환
- bump_version 자동 호출
- **변경 파일**: `src/core/server_db_manager.py`, `src/ui/server_spec_manager.py`

## 기술 선택
- UI: 기존 CustomTkinter + ttk.Treeview 패턴 유지
- 다이얼로그: AddSpecItemDialog/EditSpecItemDialog → 통합 SpecItemDialog
- DB: 기존 ServerDBManager + psycopg2 (추가 메서드만)
- 트리뷰: profile_manager.py의 display_as_tree 패턴 참조

## 리스크
- **트리뷰 재구성 복잡도**: 테이블↔트리 전환 시 Treeview 컬럼 동적 재설정 — profile_manager.py에서 검증된 패턴 사용
- **탭 동적 추가/삭제**: CTkTabview의 탭 동적 관리 — CTkTabview.add()/delete() API 활용
