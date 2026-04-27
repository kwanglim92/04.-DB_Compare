# Industrial Checklist 자동 기입(Auto-Fill) 시스템 계획서

## 개요
- **목적**: QC 검수 결과를 고객 출고용 Industrial Checklist 엑셀(411행)에 자동으로 기입하여, 사람이 손으로 G열(Measurement)을 채우면서 발생하던 누락/오기 병목을 제거한다.
- **범위**: 신규 모듈 5개(매퍼, 자동기입기, 정규화 유틸, 다이얼로그, 테스트), 기존 모듈 수정 4개(server_db_manager, sync_manager, main_window, requirements.txt), 서버 PG 스키마 확장 1개(`checklist_mappings` 테이블).
- **예상 단계 수**: 6 Phase

## 현재 상태 분석

### 기존 코드 구조 (재사용 자산)
- `ChecklistValidator` (`src/core/checklist_validator.py:31`) — 이미 구축된 *검증* 엔진. 엑셀 M열(DB_Key)을 읽어 QC 결과와 비교.
  - `_find_db_key_column()` — 헤더에서 DB_Key 컬럼 자동 감지
  - `_build_qc_lookup()` — QC 결과를 `Module.PartType.PartName.ItemName` 형식의 dot-key dict로 변환
  - `_compare_values()` — 값 비교(수치 허용오차 0.001)
- `QCComparator` (`src/core/comparator.py:13`) — DB vs Spec 비교 엔진, 결과를 `generate_report()`로 반환
- `SpecManager` (`src/core/spec_manager.py:15`) — 스펙 상속(common_base + profile)
- `SyncManager` (`src/core/sync_manager.py:22`) — PostgreSQL ↔ 로컬 JSON 캐시 동기화 패턴
- `ServerDBManager` (`src/core/server_db_manager.py:25`) — PG CRUD, SQL injection 방어
- `ChecklistReportDialog` (`src/ui/checklist_report_dialog.py:15`) — 검증 결과 시각화 UI 패턴
- `ExcelReportGenerator` (`src/utils/report_generator.py:25`) — openpyxl 기반 엑셀 생성

### 변경 필요 부분
- 검증만 하던 시스템을 **검증 + 자동기입(write-back)** 으로 확장
- M열이 거의 비어있는 실제 출고 파일에서도 동작하도록 — **DB_Key 명시 매핑 → 학습 사전 → 정규화 정확매칭 → 퍼지매칭 → 단위힌트** 5단 캐스케이드 도입
- 학습 매핑 사전을 서버 PostgreSQL에 두어 팀 공유, 로컬 캐시로 오프라인 폴백

### 첨부 엑셀(`C160112-020725_…_Rev.0.xlsx`) 분석 결과
| 영역 | 위치 | 의미 |
|---|---|---|
| 메인 시트 | `통합_(NX-Wafer 200mm)`, R2~R412 | 411개 항목, 한 행=한 항목, 병합 없음 |
| 자동기입 대상 | **G열** | I열 IF 수식이 PASS/FAIL 자동 판정 |
| 항목 식별 | B(Module) + C(Check Items, 자연어 영문) | 매핑 키 후보 |
| 매핑 컬럼 | M(DB_Key) | 411 중 1행만 채워짐 |
| **금지 영역** | A(SUBTOTAL), I(IF), G33(LINEST), 그룹헤더(`-`), 데이터검증, `표지` 시트 | 절대 쓰지 말 것 |
| 메타데이터 | `Last` 시트 L22/L25/L28/L31/L34/L37/L40/L43 | Model/SID/Ref/Date/EndUser/엔지니어 |

## 구현 계획

### Phase 1: 서버 스키마 + 동기화 인프라
- `dbmanager-server/` 초기화 스크립트에 `checklist_mappings` 테이블 DDL 추가
  - 컬럼: `id, model, module, item_norm, db_key, confidence, verified_by, verified_at, source`
  - `UNIQUE(model, module, item_norm)` upsert 키
- `src/core/server_db_manager.py` — 테이블 화이트리스트에 `checklist_mappings` 추가, CRUD 메서드(upsert, fetch_by_model, delete) 추가
- `src/core/sync_manager.py` — 매핑 사전 양방향 동기화 메서드(`sync_checklist_mappings(model)`, `_load_local_mappings()`, `_save_local_mappings()`) 추가
- 로컬 캐시 경로: `%APPDATA%/DB_Manager/cache/checklist_mappings_{model}.json`

### Phase 2: 매핑 파이프라인
- `src/utils/text_normalizer.py` (신규) — 약어 사전 + 정규화
  - 소문자화, 괄호 제거, 화이트스페이스 정리, 약어 확장(`AFM`/`Atomic Force Microscope`, `Repeat`/`Repeatability` 등)
- `src/core/checklist_mapper.py` (신규) — 5단 캐스케이드
  - (A) explicit M열 → 1.00
  - (B) 학습 사전 hit → 0.95
  - (C) 정규화 정확 일치 → 0.85
  - (D) Module 컨텍스트 + rapidfuzz 점수 ≥ 0.80 → 점수
  - (E) 단위 힌트 + Module 일치 → 0.60
  - 미매핑 행은 후보 5개 추천(rapidfuzz top-k)

### Phase 3: 자동 기입 엔진 + 안전 가드
- `src/core/checklist_autofiller.py` (신규)
- `AutoFillReport` 데이터 클래스: filled / skipped_unmapped / skipped_protected / conflicts / mapping_changes
- 안전 가드:
  1. 백업 자동 생성 (`<원본>.bak.{timestamp}.xlsx`)
  2. 금지 영역 화이트리스트 (G열 외 절대 안 씀, `표지` 시트 무시, 수식 셀 skip, 그룹 행 skip)
  3. Dry-run 기본 ON
  4. 셀 색상 표시 (녹/노/빨)
  5. `_AutoFill_Log` 시트 자동 생성
  6. 메타데이터 채우기 옵션 (Last 시트)

### Phase 4: 검수자 UI 다이얼로그
- `src/ui/checklist_autofill_dialog.py` (신규)
- `ChecklistReportDialog` 패턴 차용
- 상단 통계 바: 자동/학습/퍼지/미매핑 카운트 + 신뢰도 분포
- 트리뷰: 행번호 / Module / Item / DB_Key / QC값 / 신뢰도 / 출처 / 액션
- 미매핑 행 후보 드롭다운 + 수동 재매핑
- 하단 버튼: [Dry-run] / [확정 기입] / [M열 자동 채우기 옵션 체크박스]
- `src/ui/main_window.py` 수정 — 메뉴/버튼 진입점 추가

### Phase 5: 메타데이터 자동 채움
- `ChecklistAutoFiller._fill_metadata_sheet()` 메서드
- `Last` 시트 매핑: L22(Model) / L25(SID) / L28(Ref Doc) / L31(Date) / L34(End User) / L37/L40/L43(엔지니어)
- 데이터 출처: 활성 프로필 + 사용자 설정(`config_helper`) + 검사 일자
- 다이얼로그에서 체크박스로 ON/OFF

### Phase 6: 테스트
- `tests/test_text_normalizer.py` — 정규화/약어 단위 테스트
- `tests/test_checklist_mapper.py` — 5단 캐스케이드 분기별 테스트
- `tests/test_checklist_autofiller.py` — 첨부 파일을 픽스처로 통합 테스트
  - dry-run 결과의 출처별 카운트 검증
  - 금지 영역 셀이 변경되지 않는지 회귀 검증
  - 백업 파일 생성 검증

## 기술 선택
| 라이브러리/패턴 | 선택 이유 |
|---|---|
| `rapidfuzz` | C 구현, MIT, 빠름. 411행 × 수백 후보 매칭 성능. PyInstaller hidden import 등록 필요. |
| **서버 PG 우선** | 팀 공유 학습 즉시 가능. 기존 `SyncManager` 패턴 재사용. |
| **로컬 JSON 캐시 폴백** | 오프라인/서버 다운 시에도 매핑 사용 가능. 기존 `SpecManager` 폴백 동작과 일관. |
| **Dry-run 기본 ON** | 고객 전달 직전 파일을 다루므로 사고 방지 최우선. |
| **G열만 쓰는 화이트리스트 방식** | 수식/유효성/SUBTOTAL 등 사전 분석된 위험 셀을 절대 건드리지 않음. |

## 리스크
| 예상 문제 | 대응 |
|---|---|
| 첫 출고 파일에서 매핑 사전이 비어 있어 매칭률 저조 | 미매핑 행 후보 5개 추천 + 수동 매핑 1회 = 다음 번부터 학습됨. 사용자 검수 단계에 "매핑 작업 시간"이 포함됨을 안내. |
| 자연어 항목명 매칭 신뢰도 변동 | 신뢰도 임계값을 옵션화(`confidence_threshold`), 0.80 미만은 사용자 확인 필수. |
| openpyxl로 수식이 있는 워크북 저장 시 일부 수식 휘발 | `data_only=False`로 로드, 수식이 있는 셀은 절대 쓰기 대상에서 제외. 백업 자동 생성으로 사고 시 복원 가능. |
| 서버 다운 시 매핑 갱신 손실 | 로컬 캐시에 우선 기록 + 재시도 큐, 다음 접속 시 upsert. |
| PyInstaller 빌드에서 rapidfuzz hidden import 누락 | `DB_Compare_QC_Tool.spec`에 `hiddenimports`로 명시. 빌드 후 EXE 동작 회귀 테스트 필수. |
| 고객 전달본에 내부 DB_Key가 노출 | M열 자동 기입은 기본 OFF, 옵션 체크박스로만 활성화 → 사내 보관본 전용. |

## 핵심 수정/생성 파일

| 경로 | 종류 | 비고 |
|---|---|---|
| `dbmanager-server/` 초기화 스크립트 | 수정 | DDL 추가 |
| `src/core/server_db_manager.py` | 수정 | CRUD |
| `src/core/sync_manager.py` | 수정 | 동기화 |
| `src/core/checklist_mapper.py` | 신규 | 5단 캐스케이드 |
| `src/core/checklist_autofiller.py` | 신규 | G열 쓰기 + 안전 가드 |
| `src/utils/text_normalizer.py` | 신규 | 정규화 + 약어 |
| `src/ui/checklist_autofill_dialog.py` | 신규 | 검수자 UI |
| `src/ui/main_window.py` | 수정 | 진입점 |
| `requirements.txt` | 수정 | rapidfuzz 추가 |
| `DB_Compare_QC_Tool.spec` | 수정 | hidden import 등록 |
| `tests/test_*.py` | 신규 | 단위/통합 테스트 |

## 검증 방법
1. `pytest tests/` — 정규화/매퍼/자동기입 단위·통합 테스트 통과
2. dbmanager-server 컨테이너에 신규 DDL 적용 → 테이블 존재 확인
3. 메인 앱 실행 → QC Inspector 검사 1회 → 새 메뉴 `Industrial Checklist 자동 기입` 진입
4. 첨부 파일 로드 → 매핑 통계 확인 → Dry-run 미리보기 → 확정 기입
5. 결과 확인: 백업 파일 생성, G열 채워짐, I열 PASS/FAIL 자동 갱신, `_AutoFill_Log` 시트 생성, M열 미수정(옵션 OFF 시)
6. 회귀: 기존 `ChecklistValidator` 검증 모드 동작 변동 없음
