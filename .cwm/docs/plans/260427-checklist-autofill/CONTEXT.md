# Industrial Checklist 자동 기입 — 맥락 노트

## 결정 기록

| 결정 사항 | 선택지 | 최종 선택 | 이유 |
|---|---|---|---|
| 퍼지 매칭 라이브러리 | rapidfuzz / difflib / 둘 다 폴백 | **rapidfuzz** | C 구현 속도, MIT 라이선스, PyInstaller 빌드에 hidden import만 등록하면 됨 |
| 매핑 사전 저장소 | 로컬 JSON / 서버 PG / 둘 다 | **서버 PG 우선 + 로컬 캐시 폴백** | 팀 공유 즉시 가능, 기존 SyncManager 패턴 재사용. SpecManager 폴백 일관성 유지 |
| 엑셀 M열 자동 기입 | 기본 OFF / 기본 ON / 기능 자체 제외 | **기본 OFF, 옵션으로 ON** | 고객 전달본에 내부 DB 키 노출 방지. 사내 보관본에서만 학습 데이터로 활용 |
| LLM 매핑 후보 추천 | MVP 포함 / Phase 3 / 사내 LLM | **Phase 3 (선택)** | 외부 API 의존성 회피. rapidfuzz + 학습 사전 커버리지 먼저 측정 |
| 자동 기입 기본 모드 | Dry-run 기본 ON / 즉시 쓰기 | **Dry-run 기본 ON** | 고객 출고 직전 파일이므로 사고 방지 최우선 |
| 백업 정책 | 별도 사본 모드 / 백업 자동 생성 / 없음 | **백업 자동 생성** (`<원본>.bak.{ts}.xlsx`) | 사용자 워크플로우 변경 없이 안전성 확보 |

## 첨부 엑셀 분석 결과 — 자동화의 발판

### 시트 구성 (3개)
- `표지` — 로고/이미지 영역, 셀 값 비어있음. **자동기입 대상 아님**.
- `통합_(NX-Wafer 200mm)` — **메인 항목표 (자동기입 핵심 대상)**
  - R1 헤더, R2~R412 411개 항목, 병합 없음
- `Last` — 출고 인증서 + 일부 항목 요약 (메타데이터 자동기입 대상)

### 메인 시트 컬럼 매핑
| 컬럼 | 의미 | 자동기입 |
|---|---|---|
| A | 일련번호 (SUBTOTAL 수식) | ❌ 절대 금지 |
| B | Module (그룹 — XY Stage / AFM Head / EFEM 등 25+) | ❌ 매핑 키로만 사용 |
| C | Check Items (자연어 영문 설명) | ❌ 매핑 키로만 사용 |
| D / E / F | Min / Criteria / Max (Spec) | ❌ 데이터 검증 걸린 셀 다수 |
| **G** | **Measurement (측정값)** | ✅ **자동기입 대상** |
| H | Unit (nm/%/V/um/Hz/ea/Version 등) | ❌ 단위 힌트 매칭에만 활용 |
| I | PASS/FAIL (IF 수식) | ❌ 절대 금지 |
| J | Category (Performance / Configuration) | ❌ |
| K~O | Trend / 옵션 / DB_Key / Remark / 중간검수 | M열만 옵션 기입 |

### 안전 영역 / 금지 영역
**쓰기 OK**: G2:G412 (단, G33 LINEST 수식 제외, 그룹 행 제외)
**쓰기 OK**: Last 시트 L22 / L25 / L28 / L31 / L34 / L37 / L40 / L43
**절대 금지**: A열, I열, G33(LINEST), 그룹 헤더 행(D/E/G에 `-` 표시), 데이터 검증 걸린 51개 셀, `표지` 시트

### 메타데이터 셀 좌표 (`Last` 시트)
| 항목 | 라벨 | 값(병합) |
|---|---|---|
| Product Model | F22 | L22:V24 |
| SID Number | F25 | L25:V27 |
| Reference Document | F28 | L28:V30 |
| Date of Final Test | F31 | L31:V33 |
| End User | F34 | L34:V36 |
| Manufacturing Eng. | F37 | L37 |
| QC Eng. | F40 | L40 |
| Manager | F43 | L43 |

### 매칭 난이도 분석
- M열(DB_Key) 채워진 행: **411 중 1행** (M119 = `Dsp.ZDetector.LongHead.MicrometerPerAdcHigh`)
- C열은 자연어 영문 설명 (예: `AFM, Static Repeatability w/ 180nm Step Height Sample (15 repeats, 1σ)`)
- 직접 일치 추정: 30~50%
- → 5단 캐스케이드 + 학습 사전 + 사용자 검수가 필수

## 재사용 자산 (코드)

| 파일 / 함수 | 재사용 방식 |
|---|---|
| `src/core/checklist_validator.py:165` `_find_db_key_column()` | M열 자동 감지 — 신규 매퍼에서도 동일 사용 |
| `src/core/checklist_validator.py:187` `_build_qc_lookup()` | QC 결과 dot-key dict 변환 — 신규 자동기입기에서 그대로 사용 |
| `src/core/checklist_validator.py:198` `_compare_values()` | 값 비교 (수치 허용오차) — Dry-run 미리보기 시 비교에 활용 |
| `src/core/sync_manager.py:22` SyncManager 패턴 | 매핑 사전 동기화 메서드 추가 시 동일 패턴 |
| `src/core/server_db_manager.py:25` ServerDBManager | 테이블 화이트리스트 + CRUD 패턴 그대로 |
| `src/ui/checklist_report_dialog.py:15` ChecklistReportDialog | 신규 다이얼로그의 UI 패턴/스타일 차용 |
| `src/utils/format_helpers.py:8` `format_spec()` | 다이얼로그에서 Spec 표시 시 |
| `src/constants.py` `EXCEL_COLORS` | 셀 색상 표시(녹/노/빨)에 사용 |

## 참조 자료
- 승인된 plan 파일 원본: `C:\Users\Spare\.claude\plans\c-users-spare-desktop-c160112-020725-hu-wobbly-key.md`
- 분석 대상 출고용 엑셀: `C:\Users\Spare\Desktop\C160112-020725_Huahong Grace Fab3 #2_NX-Wafer 200mm_Industrial Checklist_2026-Q1-Rev.0.xlsx`
- 관련 메모리: `project_next_feature.md` (서버 DB 동기화 — 같은 패턴 활용), `project_server_infra.md` (PG 5434, pgAdmin 5050)
- 기존 검증 다이얼로그 UX: `src/ui/checklist_report_dialog.py:15`

## 제약 조건
- **사내 환경**: 외부 LLM API 호출은 정책 미확인 → MVP 제외
- **PyInstaller 빌드**: 신규 의존성은 spec 파일에 hidden import 등록 필요. 빌드 사이즈 약 2~3MB 증가 허용
- **서버 환경**: PostgreSQL 5434, Docker Compose 별도 스택. 기존 `specs`/`profiles` 테이블과 같은 DB에 `checklist_mappings` 추가
- **고객 전달본 무결성**: 자동 기입 후 파일이 기존 수식/판정 로직(I열 IF)을 깨뜨리지 않아야 함. G열만 채우고 나머지는 절대 건드리지 않음
- **오프라인 동작 필수**: 서버 미설정/접속 불가 환경에서도 검사 + 자동 기입이 동작 (로컬 캐시 폴백)

## 사용자 요구사항 원문

> DB Manager 의 가장 큰 병목은 이렇게 현재 사용하고 있는 장비 PC 에 DB 값 또는 이 값을 백업해놓은 서버에서 DB 를 분석해서 정해진 항목들을 QC 검사 하는데 그치지 않고, 이 값들을 고객에게 오피셜한 문서로 제공하는 Check list 즉 엑셀 보고서에 값을 누락 하는 경우나 값을 잘못 입력하는 경우야.
>
> 그래서 아이디어를 듣고 싶어. 이렇게 엑셀 형태로 Item 이름이 동일 하다면 아니면 어느정도 유사 하다면, 실제로 그 항목에 맞춰서 QC 검수가 완료된 값을 자동으로 기입해주는 시스템은 어때?
>
> 실제 장비 출고시 최종 작성되는 Check list 파일을 첨부했어.
>
> 자료 구조를 살펴보면 실제 서버 DB 값과 유사한 값들이 보일꺼야.
>
> 그러니깐 처음부터 살펴보면 장비 DB 셋팅을 잘 했는지, 그리고 그 DB 값을 백업해놓은 파일을 서버에 잘 격납 했는지, 그 DB 셋팅 값들을 Check list 에 잘 기입했는지 까지를 보는게 QC 검수에 처음과 끝이야.
>
> 이 작업을 사람이 하나하나 일일히 확인 한 부분을 지금 프로그램 개발을 통해서 어느정도 자동화가 되었는데, 최종 문서 QC 까지 자동화 및 확인 할 수 있도록 여러가지 아이디어를 제안 해줘.
