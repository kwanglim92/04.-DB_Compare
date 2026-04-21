# Server Spec Manager 기능 강화 체크리스트

## Phase 1: Add/Edit 다이얼로그 UI 최적화
- [x] 1.1 AddSpecItemDialog + EditSpecItemDialog → SpecItemDialog 통합
- [x] 1.2 컴팩트 그리드 레이아웃 (420x400)
- [x] 1.3 validation_type 변경 시 필드 동적 표시/숨김
- [x] 1.4 로컬 검증 (앱 실행 → 추가/편집 테스트)

## Phase 2: 트리 뷰 모드 추가
- [x] 2.1 테이블/트리 뷰 토글 스위치 추가 (툴바)
- [x] 2.2 트리 뷰 렌더링 (Module > PartType > PartName > Item)
- [x] 2.3 아이콘 + 항목 수 카운트 표시
- [x] 2.4 Treeview 컬럼 동적 재구성 (테이블 8열 ↔ 트리 3열)
- [x] 2.5 트리 뷰에서 더블클릭 편집 동작

## Phase 3: 검색 강화 + 우클릭 메뉴
- [x] 3.1 검색 하이라이트 (매칭 항목 오렌지 배경)
- [x] 3.2 우클릭 컨텍스트 메뉴 (편집/삭제/경로 복사)
- [x] 3.3 트리 뷰 + 테이블 뷰 양쪽에서 동작 확인

## Phase 4: 프로필 CRUD (서버 DB)
- [x] 4.1 ServerDBManager에 프로필 생성/이름변경/삭제 메서드 추가
- [x] 4.2 프로필 추가 UI (+ 버튼 또는 메뉴)
- [x] 4.3 프로필 이름 변경 UI
- [x] 4.4 프로필 삭제 UI (CASCADE 삭제 확인)
- [x] 4.5 탭 동적 추가/제거 동작 확인

## Phase 5: Import/Export
- [x] 5.1 Export 기능 (현재 탭 → JSON 파일)
- [x] 5.2 Import 기능 (JSON 파일 → 서버 DB)
- [x] 5.3 기존 Profile Manager export 포맷과 호환 확인
- [x] 5.4 bump_version 자동 호출 확인

## 컨텍스트 전환 체크
- [x] 사용자 승인 완료
- [x] /compact 안내 출력 완료

## 품질 체크
- [x] 기존 66개 테스트 회귀 통과
- [ ] 서버 연결 CRUD 동작 확인
- [ ] 오프라인 모드에서 기존 Profile Manager 정상 동작 확인
