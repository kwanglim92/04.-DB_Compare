# DB_Manager 빌드 전 정리 — 문서 통합 + 코드 최적화 계획서

## 개요
- **목적**: v1.6 (Auto-Fill) 빌드/배포 전 누적 부채 정리. PRD를 v1.5.x까지 갱신, 중복 문서 통합, 컬럼 상수 단일화, 레거시 자산 제거.
- **범위**: `docs/` 7개 파일 정리, `src/constants.py` + `src/utils/checklist_helpers.py` 신규/수정, 3개 checklist 모듈 리팩터, `_deprecated/`·`legacy.json` 삭제, `.spec` 점검.
- **예상 단계 수**: 3 Phase (문서 → 코드 → 검증)

## 현재 상태 분석

### 문서 (`docs/`)
| 파일 | 상태 | 문제 |
|---|---|---|
| `PRD_DB_Manager_v1.1.0.md` | v1.1.0 (2026-03-11) | 4개 마이너 버전 미반영 |
| `user_workflow.md` | v1.1.0 | 사용설명서.md와 50% 중복, outdated |
| `profile_manager_workflow.md` | v1.1.0 | v1.3 Admin 통합 미반영 |
| `사용설명서.md` | v1.5.2 | 최신 — 다른 두 워크플로우를 흡수할 베이스 |
| `README.md` | v1.0 badge | 버전 표기 불일치 |
| `CHANGELOG.md` | v1.5.2 | 손대지 않음 |
| `final_checklist_qc_verification.md` | v1.5.0 | 손대지 않음 |

### 코드 (`src/`)
- 엑셀 컬럼 상수 3중 정의: `checklist_validator.py`(`MODULE_COL`/`ITEM_COL`/...), `checklist_autofiller.py`(`_COL_MODULE`/...), `checklist_final_qc.py`(`COL_MODULE`/...)
- `ChecklistValidator._build_qc_lookup`, `_find_db_key_column` private 메서드가 cross-class로 호출됨
- `src/ui/_deprecated/` 96KB, `config/qc_specs_legacy.json` 40KB
- `.spec` hidden imports 일부 미검증

### 변경 필요 부분
- 문서: 5파일 갱신, 2파일 삭제, 1파일 리네임
- 코드: 1상수 그룹 추가, 1유틸 신규, 3모듈 리팩터, 2자산 삭제

## 구현 계획

### Phase 1: 문서 정리
- 1-1. PRD 갱신 + 리네임 → `PRD_DB_Manager.md`
- 1-2. 워크플로우 2개 → 사용설명서.md로 흡수 후 삭제
- 1-3. README badge + 링크 정리

### Phase 2: 코드 최적화
- 2-1. `src/constants.py`에 `CHECKLIST_COLS` 추가 + 3모듈 참조로 변경
- 2-2. `src/utils/checklist_helpers.py` 신규 — `build_qc_lookup`, `find_db_key_column`
- 2-3. `.spec` hidden imports 점검
- 2-4. `_deprecated/`·`legacy.json` 삭제 (import check 후)
- 2-5. `.gitignore` 점검

### Phase 3: 검증
- pytest 회귀 (147 passed, 3 skipped 유지)
- `python main.py` 수동 검증
- (옵션) `build.bat` 빌드 검증

## 기술 선택
- **컬럼 상수 단일화**: dict 형태 (`CHECKLIST_COLS['MODULE']`) — 기존 `EXCEL_COLORS` 패턴과 일관
- **헬퍼 추출 + 위임**: 기존 `ChecklistValidator` 메서드는 신규 함수에 위임하여 외부 호환 유지
- **Git history**: 삭제된 파일 git log로 복구 가능 → 백업 파일 별도 생성 안 함

## 리스크
| 예상 문제 | 대응 |
|---|---|
| 컬럼 상수 통합 중 호출처 누락 | grep으로 `_COL_`, `COL_` 패턴 전수 확인 + pytest 통과 |
| 워크플로우 문서 디테일 누락 | 삭제 전 두 파일 내용을 사용설명서와 diff |
| `_deprecated/` 어딘가에서 import | 삭제 전 `grep -r "_deprecated"` 확인 |
| `.spec` hidden import 제거 후 ImportError | EXE 빌드 후 회귀 검증, 문제 시 즉시 복원 |

## 핵심 수정/생성 파일

| 경로 | 종류 |
|---|---|
| `docs/PRD_DB_Manager.md` | 신규 (v1.1.0 삭제 후) |
| `docs/PRD_DB_Manager_v1.1.0.md` | 삭제 |
| `docs/user_workflow.md` | 삭제 |
| `docs/profile_manager_workflow.md` | 삭제 |
| `docs/사용설명서.md` | 수정 |
| `docs/README.md` | 수정 |
| `src/constants.py` | 수정 (`CHECKLIST_COLS` 추가) |
| `src/utils/checklist_helpers.py` | 신규 |
| `src/core/checklist_validator.py` | 수정 |
| `src/core/checklist_autofiller.py` | 수정 |
| `src/core/checklist_final_qc.py` | 수정 |
| `src/ui/_deprecated/` | 삭제 (디렉토리) |
| `config/qc_specs_legacy.json` | 삭제 |
| `DB_Compare_QC_Tool.spec` | 수정 |

## 검증 방법
1. `python -m pytest -q` → 147 passed, 3 skipped 유지
2. `python main.py` → 앱 정상 시작 + Auto-Fill 다이얼로그 진입
3. (옵션) `build.bat` → EXE 정상 생성, 빌드 사이즈 비교
