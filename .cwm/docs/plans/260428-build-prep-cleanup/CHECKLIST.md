# 빌드 전 정리 — 체크리스트

## 작업 목록

### Phase 1: 문서 정리
- [x] PRD 갱신 + 리네임
  - [x] 헤더 표 (현재 버전 v1.5.1, 최종 수정일 2026-04-28)
  - [x] §2.3 현재 기능 요약 — v1.2~v1.5 신기능 추가
  - [x] §8.2 v1.2 요구사항 R8~R12 → ✅ 완료
  - [x] §8.3 R14·R17 완료 표시
  - [x] §10 Roadmap — v1.2~v1.5 완료 행, v1.6 신규 행
  - [x] §13 Timeline — v1.2 Phase 6까지 완료, v1.6 신규
  - [x] §16.C 변경 이력 — v2.0 (2026-04-28) 추가
  - [x] `PRD_DB_Manager_v1.1.0.md` 삭제, `PRD_DB_Manager.md` 생성
- [x] 워크플로우 문서 통합
  - [x] `user_workflow.md` 내용 분석 → 사용설명서.md에 흡수
  - [x] `profile_manager_workflow.md` 내용 분석 → 사용설명서.md에 흡수
  - [x] 사용설명서.md 헤더 버전 v1.5.1로 갱신
  - [x] §3.1.3에 결과 상태 + 검증 방식 표 보강
  - [x] §4 Profile Manager → v1.3+ Admin 모드로 갱신
  - [x] 새 §8 대표 시나리오 추가 (6개)
  - [x] 새 §9 v1.6 Auto-Fill 안내 추가
  - [x] 추가 자료 PRD 링크 갱신
  - [x] `user_workflow.md` 삭제
  - [x] `profile_manager_workflow.md` 삭제
- [x] README 갱신
  - [x] 버전 배지 → v1.5.1
  - [x] 슬림 재작성 (v1.5.1 기능 요약 표 + 사용설명서로 위임)
  - [x] 비밀번호 (`pqc123`/`pqclevi`) 명시
  - [x] PRD 링크 수정 (`PRD_DB_Manager.md`)

### Phase 2: 코드 최적화
- [x] `src/constants.py`에 `CHECKLIST_COLS` dict 추가
- [x] `src/utils/checklist_helpers.py` 신규
  - [x] `build_qc_lookup(qc_report)` 함수
  - [x] `find_db_key_column(ws)` 함수
- [x] `src/core/checklist_validator.py` 수정
  - [x] 클래스 상수 → `CHECKLIST_COLS` 참조
  - [x] `_build_qc_lookup` → 신규 헬퍼 위임
  - [x] `_find_db_key_column` → 신규 헬퍼 위임
- [x] `src/core/checklist_autofiller.py` 수정 — `_COL_*` 모듈 상수 → `CHECKLIST_COLS`
- [x] `src/core/checklist_final_qc.py` 수정 — `COL_*` 상수 → `CHECKLIST_COLS`
- [x] PyInstaller 빌드 점검
  - [x] `.spec`은 v1.6 의존성 이미 포함 — 변경 불필요
  - [x] `build.bat`에 psycopg2 / cryptography / rapidfuzz hidden import 보강
- [x] 레거시 삭제
  - [x] `grep -r "_deprecated"` 결과 외부 참조 없음 확인
  - [x] `src/ui/_deprecated/` 디렉토리 삭제 (3 파일, 96KB)
  - [x] `config/qc_specs_legacy.json` 삭제 (40KB)
- [x] `.gitignore` 점검
  - [x] `__pycache__/`, `dist/`, `build/`, `*.egg-info/` ✅ 이미 커버
  - [x] `.pytest_cache/` 신규 추가
  - [x] `!DB_Compare_QC_Tool.spec` — 사용자 정의 spec 추적 보장

### Phase 3: 검증
- [x] `python -m pytest -q` → **152 passed, 3 skipped** (회귀 없음)
- [x] `python -c "import main"` → 깨끗하게 import
- [ ] (옵션) `build.bat` → EXE 빌드 + 사이즈 비교 (사용자 환경 별도)
- [ ] (옵션) `python main.py` → GUI 수동 검증 (사용자 환경 별도)

## 컨텍스트 전환 체크
- [x] 사용자 승인 완료 (Plan mode ExitPlanMode 통과)
- [ ] /compact 안내 (전체 작업 완료로 불필요)

## 품질 체크
- [x] 에러 처리 — `CHECKLIST_COLS` 누락 시 KeyError 자연스럽게 발생
- [x] 보안 — 삭제 파일 (deprecated UI / legacy json)에 민감 정보 없음 확인
- [x] 테스트 통과 — 152 passed (기준선 147 → +5, 회귀 없음)
- [x] 회귀 검증 — 기존 ChecklistValidator 동작 변동 없음 (위임으로 호환 유지)
- [x] 사용자 매뉴얼 / 변경 노트 업데이트 — PRD/README/사용설명서 갱신 완료
