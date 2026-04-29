# Industrial Checklist 자동 기입 — 체크리스트

## 작업 목록

### Phase 1: 서버 스키마 + 동기화 인프라
- [x] `dbmanager-server/` 초기화 스크립트에 `checklist_mappings` 테이블 DDL 추가
  - [x] 컬럼 정의: id / model / module / item_norm / db_key / confidence / verified_by / verified_at / source
  - [x] `UNIQUE(model, module, item_norm)` 제약 추가
  - [x] 인덱스: `model` 단일 컬럼 인덱스
- [x] 기존 PG 컨테이너에 신규 테이블 적용 (마이그레이션 명령) → `03_checklist_mappings.sql` 생성
- [x] `src/core/server_db_manager.py` 수정
  - [x] 테이블 화이트리스트에 `checklist_mappings` 추가
  - [x] `upsert_checklist_mapping(model, module, item_norm, db_key, ...)` 메서드
  - [x] `fetch_checklist_mappings(model)` 메서드
  - [x] `delete_checklist_mapping(id)` 메서드
- [x] `src/core/sync_manager.py` 수정
  - [x] `sync_checklist_mappings(model)` — 서버 → 로컬 캐시 갱신
  - [x] `_load_local_mappings(model)` — 캐시 JSON 로드
  - [x] `_save_local_mappings(model, data)` — 캐시 JSON 저장
  - [x] 로컬 캐시 경로: `cache/checklist_mappings_{model_safe}.json`
  - [x] 서버 다운 시 로컬 캐시 폴백 동작 확인

### Phase 2: 매핑 파이프라인
- [x] `requirements.txt`에 `rapidfuzz` 추가
- [x] `DB_Compare_QC_Tool.spec`에 `rapidfuzz` hidden import 등록
- [x] `src/utils/text_normalizer.py` (신규)
  - [x] 소문자화 / 화이트스페이스 정리 / 괄호 안 단위·조건 제거
  - [x] 약어 사전 (`AFM`/`Atomic Force Microscope`, `Repeat`/`Repeatability`, …)
  - [x] `normalize(text)` 메인 함수
  - [x] 단위 토큰 추출 함수
- [x] `src/core/checklist_mapper.py` (신규)
  - [x] `MapResult` 데이터 클래스 (db_key, confidence, source, candidates)
  - [x] (A) explicit M열 매처 → confidence 1.00
  - [x] (B) 학습 사전 매처 → confidence 0.95
  - [x] (C) 정규화 정확 일치 매처 → confidence 0.85
  - [x] (D) Module 컨텍스트 + rapidfuzz 매처 → 점수 (≥ 0.80)
  - [x] (E) 단위 힌트 + Module 일치 매처 → 0.60
  - [x] 미매핑 행 → top-5 후보 추천 (rapidfuzz)
  - [x] 신뢰도 임계값 옵션화

### Phase 3: 자동 기입 엔진 + 안전 가드
- [x] `src/core/checklist_autofiller.py` (신규)
  - [x] `AutoFillReport` 데이터 클래스 (filled / skipped_unmapped / skipped_protected / conflicts / mapping_changes)
  - [x] 옵션: `dry_run` / `fill_metadata` / `confidence_threshold` / `write_db_key_column`
  - [x] 백업 자동 생성 (`<원본>.bak.{timestamp}.xlsx`)
  - [x] 금지 영역 화이트리스트
    - [x] G열만 쓰기, 그 외 절대 금지
    - [x] `표지` 시트 무시
    - [x] 수식이 이미 있는 셀 skip (G33 LINEST 등)
    - [x] 그룹 헤더 행 skip (D/E/G에 `-` 표시)
  - [x] Dry-run 모드 — 실제 쓰기 없이 결과 리포트만
  - [x] 셀 색상 표시 (녹 #E8F5E9 / 노 #FFF8E1 / 빨 #FFEBEE)
  - [x] `_AutoFill_Log` 시트 자동 생성 (행/항목/키/신뢰도/출처/값/타임스탬프)

### Phase 4: 검수자 UI 다이얼로그
- [x] `src/ui/checklist_autofill_dialog.py` (신규)
  - [x] 모달 다이얼로그 기본 골격 (`ChecklistReportDialog` 패턴 차용)
  - [x] 상단 통계 바 (자동/학습/퍼지/미매핑 카운트 + 신뢰도 분포)
  - [x] 트리뷰 (행/Module/Item/DB_Key/QC값/신뢰도/출처/액션)
  - [x] 미매핑 행 시각 강조 (빨강 배경)
  - [x] 행별 후보 드롭다운 (top-5 추천 — candidates 필드로 전달)
  - [x] 하단 액션 버튼: [Dry-run 미리보기] / [확정 기입] / [닫기]
  - [x] 옵션 체크박스: [메타데이터 자동 채우기] / [엑셀 M열도 채우기]
- [x] `src/ui/main_window.py` 수정
  - [x] 새 버튼 진입점 추가 (`Auto-Fill Checklist`)
  - [x] QC 검사 완료 후에만 활성화

### Phase 5: 메타데이터 자동 채움
- [x] `ChecklistAutoFiller._fill_metadata_sheet()` 메서드 추가
- [x] `Last` 시트 L22 / L25 / L28 / L31 / L34 / L37 / L40 / L43 매핑
- [x] 데이터 출처: 활성 프로필 + 사용자 설정 + 검사 일자
- [x] 다이얼로그 체크박스 ON일 때만 동작
- [x] 기존 셀 값이 있으면 skip (로그 기록)

### Phase 6: 테스트
- [x] `tests/test_text_normalizer.py`
  - [x] 약어 확장
  - [x] 괄호 / 단위 / 화이트스페이스 처리
- [x] `tests/test_checklist_mapper.py`
  - [x] 5단 캐스케이드 분기별 테스트
  - [x] 신뢰도 계산
  - [x] top-5 후보 추천
- [x] `tests/test_checklist_autofiller.py`
  - [x] 첨부 엑셀(`C160112-020725_…_Rev.0.xlsx`)을 픽스처로 통합 테스트 (3 skipped — 파일 없음)
  - [x] dry-run 결과 출처별 카운트 검증
  - [x] 금지 영역 셀(A/I/G33/그룹헤더/표지) 미수정 회귀 검증
  - [x] 백업 파일 생성 검증
  - [x] `_AutoFill_Log` 시트 생성 검증
- [ ] PyInstaller 빌드 검증 — `build.bat` 실행 후 EXE에서 rapidfuzz 동작 확인 (서버 마이그레이션 완료 2026-04-27)

## 컨텍스트 전환 체크
- [x] 사용자 승인 완료
- [ ] /compact 안내 출력 완료

## 아키텍처 변경 (2026-04-28 반영)

원래 계획한 `ChecklistAutoFiller` 기반 구현에서 더 발전된 형태로 변경됨.

### 신규 구현 (계획 외)
- [x] `src/core/checklist_final_qc.py` — `ChecklistFinalQcEngine` (Preflight + 분류 + 위험도 + 사본 기입)
- [x] `src/ui/final_checklist_qc_dialog.py` — `FinalChecklistQcDialog` (검수자 승인 워크플로)
- [x] `tests/test_checklist_final_qc.py` — 엔진 테스트
- [x] `docs/final_checklist_qc_verification.md` — 수동/자동 검증 체크리스트
- [x] `src/ui/main_window.py` 버튼: `Auto-Fill Checklist` → `Final Checklist QC`
- [x] `docs/README.md` — Final Checklist QC 섹션 추가

### 잔존 파일 (현재 진입점에서 미사용)
- `src/core/checklist_autofiller.py` — 기존 엔진 (잔존)
- `src/ui/checklist_autofill_dialog.py` — 기존 다이얼로그 (잔존)

## 품질 체크
- [x] 에러 처리 적용 (서버 다운 / 파일 권한 / 손상된 엑셀) — Preflight에서 처리
- [x] 보안 검토 (SQL injection 화이트리스트, 파일 경로 검증)
- [x] 테스트 작성/통과 (Phase 6 + test_checklist_final_qc.py)
- [x] 회귀 검증 (기존 `ChecklistValidator` 검증 모드 동작 변동 없음)
- [x] 사용자 매뉴얼 / 변경 노트 업데이트 (`docs/README.md`, `docs/final_checklist_qc_verification.md`)
- [ ] PyInstaller 빌드 검증 — rapidfuzz 동작 확인
- [x] `test_checklist_final_qc.py` 전체 통과 확인 — 12/12 passed (2026-04-28)
