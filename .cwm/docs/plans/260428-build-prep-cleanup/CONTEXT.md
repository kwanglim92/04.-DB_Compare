# 빌드 전 정리 — 맥락 노트

## 결정 기록

| 결정 사항 | 선택지 | 최종 선택 | 이유 |
|---|---|---|---|
| PRD 파일명 | v1.5.0 갱신 / 버전 제거 / 유지 | **버전 제거 → `PRD_DB_Manager.md`** | 마이너 버전마다 파일명 바꾸지 않아도 됨, 영구 사용 |
| 워크플로우 문서 처리 | 갱신 / 통합 후 삭제 / 그냥 삭제 | **사용설명서로 통합 후 삭제** | 사용설명서가 이미 7장으로 상세하게 커버 중, 단일 진실 공급원 확립 |
| 레거시 자산 처리 | 삭제 / 일부 보존 / 모두 보존 | **둘 다 삭제 (`_deprecated/`, `qc_specs_legacy.json`)** | git history로 복구 가능, v1.3+ 모두 신규 구조로 운영 중 |
| 컬럼 상수 통합 방식 | dict / Enum / 클래스 상수 | **dict (CHECKLIST_COLS)** | 기존 `EXCEL_COLORS` 패턴과 일관, 가벼운 라이브러리 의존 없음 |
| 기존 호출자 호환성 | breaking change / 위임 | **위임 (소프트 디프리케이션)** | 기존 `ChecklistValidator._build_qc_lookup` 외부 호출자 보호, 점진적 이전 |

## 첨부 분석 결과

### 코드 컬럼 상수 3중 정의 위치
- `src/core/checklist_validator.py:35-38` — `ITEM_COL=3`, `VALUE_COL=7`, `MODULE_COL=2`, `DB_KEY_COL=13`
- `src/core/checklist_autofiller.py` — `_COL_MODULE=2`, `_COL_ITEM=3`, `_COL_VALUE=7`, `_COL_UNIT=8`, `_COL_PASS=9`, `_COL_DB_KEY=13`
- `src/core/checklist_final_qc.py` — `COL_*` 상수들

### 신규 호출자
- `checklist_autofill_dialog.py` — `_build_qc_lookup` 호출
- `checklist_final_qc.py` — `_build_qc_lookup` 호출
- `checklist_autofiller.py` — `ChecklistValidator()._build_qc_lookup()` 호출

### 레거시 자산 사이즈
- `src/ui/_deprecated/`: 96KB (profile_manager.py, profile_editor.py)
- `config/qc_specs_legacy.json`: 40KB
- 합계 ~136KB가 EXE 빌드에 포함됨

## 재사용 자산 (코드)

| 파일 / 함수 | 재사용 방식 |
|---|---|
| `src/constants.py` `EXCEL_COLORS` | dict 패턴 그대로 차용 |
| `ChecklistValidator._build_qc_lookup` | 함수로 추출 → 클래스 메서드는 위임만 |
| `ChecklistValidator._find_db_key_column` | 함수로 추출 → 클래스 메서드는 위임만 |
| `.cwm/docs/plans/` 6개 완료 플랜 | PRD §2.3·§8·§10 갱신 시 변경 내용 출처 |
| `docs/CHANGELOG.md` | v1.0~v1.5.2 변경 요약을 PRD 표에 인용 |

## 참조 자료
- `docs/PRD_DB_Manager_v1.1.0.md` — 베이스라인 PRD 구조
- `docs/사용설명서.md` — 7장 구조 그대로 유지하며 워크플로우 흡수
- `src/utils/version.py` `APP_VERSION = "1.5.1"` — 모든 문서 버전 표기 기준
- 완료된 플랜 6개:
  - `260413-server-db-sync` (v1.3.0)
  - `260414-server-spec-manager-enhance`
  - `260421-admin-mode-consolidation` (v1.3.0)
  - `260421-usability-search-import-filter` (v1.4.0)
  - `260427-v1.5-search-nav-folder-update-template` (v1.5.0)
  - `260427-checklist-autofill` (v1.6 진행 중)

## 제약 조건
- **코드 호환성**: 외부에서 `ChecklistValidator._build_qc_lookup`을 직접 호출하는 코드를 깨지 말 것 (위임 유지)
- **테스트 회귀 금지**: 현재 147 passed, 3 skipped 기준선을 유지
- **빌드 검증 후순위**: PyInstaller 빌드는 옵션 (사용자 환경에서 별도 실행)
- **git 안전**: 삭제된 파일은 git log로 복구 가능해야 함 — `--no-verify` 등으로 강제 삭제 금지

## 사용자 요구사항 원문

> 현재 전체 코드에서 이제 중복 코드나 빌드 및 배포 하기 전 최적화를 진행 하고 싶어.
>
> @docs 에 문서들도 이제 필요 없는것들은 삭제하고, 중복된 내용들은 하나로 합쳐줘. @docs/PRD_DB_Manager_v1.1.0.md 업데이트 진행.
