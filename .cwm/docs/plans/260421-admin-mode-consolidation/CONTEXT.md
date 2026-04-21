# CONTEXT: 관리자 모드 통합

## 배경
v1.2(Server DB Sync) 구현 완료 후 실사용 검토 결과, 다음 두 가지 UX 이슈가 도출되었다.

1. **Profile Manager와 Server DB 기능 중복**
   - 두 진입점 모두 Spec 편집(CRUD/트리·테이블/검색/Import·Export) 제공
   - Single Source of Truth 원칙 위반 → 로컬 편집 시 서버 미반영으로 엔지니어 간 Spec 불일치 위험

2. **생산엔지니어의 오조작 리스크**
   - 메인 창에 `Server` 버튼이 노출되어 있어, 생산엔지니어가 의도치 않게 서버 접속 설정 변경 또는 Spec 수정 가능
   - 역할(조회·QC 실행 vs Spec 관리)이 UI에서 구분되지 않음

## 결정 사항 (사용자 승인)
- **Profile Manager 제거**: `_deprecated/`로 이동 (복구 여지 유지)
- **서버 설정 + Spec 관리 통합**: 단일 AdminWindow에 탭으로 묶음
- **비밀번호 인증**: `pqc123` (사용자 지정, 기존 `pqclevi`와 분리)
- **Admin 버튼 위치**: 메인 상단 툴바 우측
- **Online/Offline 인디케이터**: 메인에 유지 (표시 전용)
- **오프라인 모드 편집**: 읽기 전용 (편집은 온라인 상태에서만)
- **버전**: v1.3.0 (MINOR bump)

## 사용자 페르소나별 흐름 (After)
- **생산엔지니어 (P1)**: Open DB → Profile 선택 → Run QC → Export (Admin 버튼 클릭 불가)
- **QC 팀 리드 (P2)**: Admin 버튼 → 비밀번호(`pqc123`) → 서버설정/Spec 관리 탭에서 작업

## 제약
- 기존 Server DB Sync 기능(v1.2) 동작 유지 — 리팩터링만 수행
- SpecManager 인터페이스 무변경 (PRD §8.2 R12)
- 오프라인 폴백 동작 유지 (PRD §8.2 R10)

## 참고
- PRD: `docs/PRD_DB_Manager_v1.1.0.md` (§6 Personas, §8 Requirements)
- 선행 플랜: `260413-server-db-sync`, `260414-server-spec-manager-enhance`
