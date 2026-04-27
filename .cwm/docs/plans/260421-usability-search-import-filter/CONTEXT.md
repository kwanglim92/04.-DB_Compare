# CONTEXT: 사용성 강화 (검색 / 임포트 / 결과 필터) — v1.4.0

## 배경
v1.3.0 (Admin 모드 통합) 실사용 결과 다음 세 가지 운영 비효율 도출:

1. **DB 트리 탐색 비효율**: 2,600+ 항목 트리에서 특정 Item 찾기 어려움 (수동 스크롤)
2. **신규 프로필 작성 시 자료구조 일관성 위험**: 모듈 추가가 1건씩 수동 입력만 가능 — 엔지니어마다 Module/PartType/PartName/ItemName을 수기 입력하면 오타·구조 불일치
3. **QC 결과 검토 비효율**: PROFILE VIEWER에 모든 항목이 한꺼번에 표시되어 Fail 항목만 보고 싶을 때 수동 스크롤

## 사용자 결정 사항
- F1: 하이라이트 + 자동 펼침/스크롤 (필터 X)
- F2 충돌 기본값: **Skip** (기존 항목 보존)
- F2 임포트 소스: **3가지 모두** (DB 폴더 + Common Base + 다른 Profile, 단일 다이얼로그 라디오 전환)
- F3 필터 UI: **Segmented Button** `[ All | Pass | Check | Fail ]`

## 제약
- v1.3.0 Admin 모드 / Server DB Sync 동작 변경 금지
- `ServerSpecManagerPanel.read_only=True` (오프라인) 시 임포트 비활성
- ttk.Treeview iid 직렬화 불가 — 메타데이터 별도 dict 관리
- 기존 66개 테스트 회귀 통과 필수

## 참고
- 본 플랜의 Plan-mode 사본: `~/.claude/plans/1-db-mutable-raccoon.md`
- 선행 플랜: `260421-admin-mode-consolidation` (v1.3.0 Admin 통합)
- 재사용 자산: `_deprecated/profile_editor.py`의 "Add Items from DB" 패턴
