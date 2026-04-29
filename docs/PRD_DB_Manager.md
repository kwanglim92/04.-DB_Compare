# DB_Manager 제품 요구사항 정의서 (PRD)

| 항목 | 내용 |
|------|------|
| **제품명** | DB_Manager (舊 DB_Compare) |
| **현재 버전** | v1.5.1 (+ v1.6 Final Checklist QC 작업 브랜치) |
| **릴리즈일** | 2026-04-27 |
| **문서 버전** | 2.1 |
| **최종 수정일** | 2026-04-29 |
| **작성자** | Levi.Beak (XE Service QC Team) |
| **대상 독자** | 경영진 / 사업부 리더 / 투자 의사결정자 |
| **분류** | 사내 전용 (External distribution prohibited) |

---

## 1. Executive Summary

DB_Manager는 **Park Systems XE Service의 장비 DB 품질검사(QC)를 자동화**하는 사내 전용 데스크톱 도구다. 기존 수작업으로 수행되던 2,600개 이상 DB 항목 검증을 **수분 내 자동화**하여 QC 엔지니어의 공수를 단축하고 휴먼에러를 제거한다.

**v1.0(2025-12-26) 최초 릴리즈 이후 4개월간 v1.5.1까지 진화**하여, 단순 검증 도구에서 **서버 기반 Spec 동기화 + 검색·임포트·자동업데이트·리포트 템플릿 + Final Checklist QC(v1.6 진행)** 까지 포괄하는 QC 운영 도구로 자리잡았다. 다음 단계는 **v1.6 Final Checklist QC / Approved Auto-Fill**로, QC 워크플로우의 마지막 병목인 "완성 checklist 최종 검수와 G열 오기입 보정"을 원본 보존 방식으로 해결한다.

### 핵심 비즈니스 임팩트 (실측 + 추정)

| 지표 | As-Is (수작업) | v1.0 (최초) | v1.5 (현재) | v1.6 (진행 중) |
|------|---------------|--------------|--------------|---------------|
| 장비 1대당 QC 소요 시간 | 2~4 시간 | 30~45 분 | 10~15 분 | **5~10 분** |
| Spec 배포 주기 | 이메일/수동 | EXE 재배포 | **실시간 동기화 (PG)** | 동일 |
| 검수 휴먼에러 발생률 | 체감 높음 | 근사 0 | 근사 0 | 근사 0 |
| **출고 엑셀 G열 오기입율** | 수기 입력 (체감 5~10%) | 동일 | 동일 | **Final QC + 승인 행 자동기입 + 재검수로 근사 0** |
| QC 엔지니어 공수 절감 | — | 약 60% | **약 85%** | **약 90%+** |

---

## 2. Product Overview (v1.5.1 현황)

### 2.1 제품 정의
Park Systems XE Service DB(XML 기반)를 파싱하여 사전 정의된 QC 프로파일과 비교하고, Excel 리포트를 자동 생성하며, 고객 출고용 Industrial Checklist 엑셀을 최종 검수한 뒤 승인된 행만 내부 결과 사본에 자동 기입하는 Windows 데스크톱 애플리케이션.

### 2.2 기술 스택
- **언어/런타임**: Python 3.11+
- **UI**: CustomTkinter (Dark/Light 테마)
- **리포트**: OpenPyXL (Excel 3-시트 + Cover Page 옵션)
- **서버**: PostgreSQL 16 (사내 Docker, 포트 5434) + pgAdmin 4 (5050)
- **퍼지 매칭**: rapidfuzz (v1.6 신규, MIT 라이선스)
- **배포**: PyInstaller 단일 EXE + NSIS 설치 프로그램
- **설정**: JSON (Common Base + Equipment Profiles 상속) + PG 동기화

### 2.3 현재 기능 요약 (v1.5.1)

| 영역 | 기능 | 도입 |
|------|------|------|
| **DB 파싱** | XML 계층 구조 자동 파싱 (Module → Part Type → Part → Item) | v1.0 |
| **검증 엔진** | 3종 검증 타입: Range(Min/Max), Exact(일치), Check(기록) | v1.0 |
| **프로파일 관리** | Common Base 상속 구조, 듀얼 뷰(Table/Tree), 실시간 검색, 미설정 항목 필터, CRUD | v1.0~v1.6 |
| **Add Items from DB** | 기존/신규 항목 시각 구분, 실시간 카운트 | v1.1 |
| **Common Base 편집** | 관리자 비밀번호로 직접 편집 | v1.1 |
| **N/A Items Review** | DB 누락 자동 감지 + 별도 리뷰 다이얼로그 | v1.1 |
| **QC 실행** | 트리뷰 컬러코딩 (Pass/Fail/Check), 요약 카운트 | v1.0 |
| **리포트** | 3-시트 Excel (Summary / All Items / Failed Items) + Cover Page | v1.0, v1.5 |
| **🆕 Server DB Sync** | PostgreSQL 직결, 로컬 JSON 캐시 폴백, 오프라인 모드 | **v1.2** |
| **🆕 Admin 통합** | 단일 비밀번호로 서버 설정 + Spec 관리 + 리포트 템플릿 통합 | **v1.3** |
| **🆕 DB 검색** | 메인 트리에 250ms 디바운스 검색, 자동 펼침/하이라이트 | **v1.4** |
| **🆕 모듈 일괄 임포트** | DB 폴더 / Common Base / 다른 Profile에서 모듈 단위 가져오기 (3가지 충돌 전략) | **v1.4** |
| **🆕 결과 필터/검색** | Profile Viewer Segmented Button (All/Pass/Check/Fail) + 전체 컬럼 검색 | **v1.4~v1.6** |
| **🆕 검색 매치 네비게이션** | F3/Shift+F3, ▲/▼ 버튼, 카운트 라벨 (현재/총) | **v1.5** |
| **🆕 Open DB 보강** | 마지막 경로 기억, 권한 에러 graceful skip, 깊이 제한 재귀, 4상태 안내 | **v1.5** |
| **🆕 자동 업데이트 체크** | PostgreSQL `app_releases` 테이블 기반, 강제/일반 모드, "이 버전 무시" | **v1.5** |
| **🆕 리포트 템플릿** | 회사 정보/타이틀 placeholder/색상/시트 구성 커스터마이징 | **v1.5** |
| **🆕 Checklist 검증** | Excel M열(DB_Key) 기반 검증 + Export DB Keys (사내 정책 옵션) | v1.4 (옵션 활성화) |
| **🆕 Final Checklist QC** | checklist 최종 검수, Profile Coverage, 승인 행 G/M열 자동기입, `_AutoFill_Log` | **v1.6 (진행 중)** |
| **보안** | 관리자 비밀번호 보호(`pqc123`/`pqclevi`), 원본 DB 읽기전용, 자격증명 암호화 | v1.0~v1.3 |

---

## 3. Problem Statement

### 3.1 현재의 문제
1. **수작업 QC의 비효율**: XE Service 장비 1대당 2,000개가 넘는 DB 항목을 엔지니어가 수작업으로 검토하며, 1대당 수 시간이 소요됨. → **v1.0~v1.5에서 해결**
2. **휴먼에러 리스크**: 수작업 검증에서 발생하는 누락·오판정은 장비 출하 후 고객사 현장 이슈로 직결됨. → **v1.0~v1.4에서 해결**
3. **Spec 관리의 파편화**: 장비별 QC 기준(Spec)이 엔지니어마다 다른 파일/기억에 산재. → **v1.2~v1.3에서 해결 (서버 동기화 + Admin 통합)**
4. **Spec 배포 병목**: Spec 변경 시마다 EXE를 재빌드·재배포해야 해서 긴급 수정이 어려움. → **v1.2에서 해결**
5. **🆕 출고 문서 오기입 (마지막 병목)**: QC가 자동화되어도 고객 전달용 Industrial Checklist 엑셀(411행)에 G열을 사람이 손으로 채우면서 누락·오기입 발생. → **v1.6에서 해결 진행 중**

### 3.2 영향 범위
- **직접 영향**: XE Service QC 엔지니어 (주사용자), QC 팀 리드, Spec 관리자
- **간접 영향**: 장비 출하 품질 → 고객 만족도 및 A/S 비용

### 3.3 미해결 시 비용
- QC 엔지니어 인건비 및 출하 지연
- 필드 불량에 따른 **A/S 출동 비용** 및 **브랜드 신뢰 저하**
- 출고 문서 오기입에 따른 **재발행 비용** 및 **고객 신뢰 손상** (v1.6 미해결 시)

---

## 4. Strategic Goals

1. **QC 공수 절감**: 장비 1대당 QC 소요 시간을 수작업 대비 **80% 이상 단축** (✅ 달성: 85%, v1.6 후 90%+ 목표).
2. **품질 표준화**: Spec 중앙화를 통해 전사 QC 기준의 **단일 진실 공급원(Single Source of Truth)** 확립 (✅ v1.2~v1.3 달성).
3. **출하 품질 지표 개선**: 출하 후 DB 설정 오류에 기인한 필드 이슈를 **전년 대비 50% 감소** (측정 진행 중).
4. **운영 효율화**: Spec 변경 시 EXE 재배포 없이 **실시간 반영** (✅ v1.2 달성).
5. **출고 문서 무결성**: Industrial Checklist 엑셀을 최종 검수하고 승인된 행만 내부 사본에 자동 기입해 **수기 오기입 0건**을 목표로 한다 (v1.6).
6. **이력 추적성 확보**: QC 결과의 **히스토리 저장 및 조회**를 통해 감사·트렌드 분석 기반 마련 (v2.0+).

---

## 5. Non-Goals

| 제외 항목 | 사유 |
|-----------|------|
| XE Service DB 이외의 타 제품군 지원 | 초기 ROI 불명확 — 별도 이니셔티브로 분리 |
| 실시간 협업 편집 (동시 다중 사용자 편집) | 사용자 규모(QC 엔지니어 수명)에 비해 복잡도 과다 |
| 외부 고객사 배포/SaaS화 | 사내 품질관리 도구이며 외부 공개 시 영업기밀 노출 리스크 |
| 장비 펌웨어·제어 기능 통합 | 제품 범위 초과 — QC 검증에 집중 |
| 모바일/웹 클라이언트 | 사용 환경이 엔지니어 PC 고정이며 ROI 낮음 |
| EXE 자동 교체 (자동 업데이트) | 보안 정책상 다운로드 링크만 제공, 사용자 수동 실행 (v1.5 결정) |
| LLM 기반 매핑 (v1.6) | 외부 API 의존성 회피 — rapidfuzz + 학습 사전으로 충분성 우선 검증 |

---

## 6. User Personas

### P1. QC 엔지니어 (주사용자)
- **역할**: 출하 장비의 DB를 검증하고 리포트 제출, 출고용 Checklist 작성
- **Pain**: 반복적·장시간 수작업, 휴먼에러 부담, 엑셀 수기 입력
- **기대**: 로드→실행→리포트→Final Checklist QC→승인 적용의 흐름

### P2. QC 팀 리드 (관리자)
- **역할**: Spec 관리, 품질 지표 모니터링, 리포트 템플릿 관리
- **Pain**: Spec 개정 시 배포 어려움, 히스토리 부재, 매핑 사전 관리
- **기대**: 중앙 Spec 관리, 팀 단위 품질 대시보드, 매핑 학습 자동화

### P3. 현장 서비스 엔지니어 (부차 사용자, 미래)
- **역할**: 고객사 설치 현장에서 DB 설정 점검
- **기대**: 오프라인 환경에서도 동작 (✅ v1.2 폴백으로 충족), 간단한 리포트 공유

---

## 7. Key User Stories

**QC 엔지니어 관점**
- QC 엔지니어로서, DB 폴더 하나만 선택하면 **프로파일 기준으로 자동 검증**되기를 원한다 (✅ v1.0).
- QC 엔지니어로서, 실패 항목만 필터링된 Excel 리포트를 즉시 받기를 원한다 (✅ v1.0).
- QC 엔지니어로서, **DB에 누락된 항목(N/A)** 을 자동 감지받기를 원한다 (✅ v1.1).
- QC 엔지니어로서, 2,600+ 항목에서 **검색으로 빠르게 점프**하고 싶다 (✅ v1.4 + v1.5 네비).
- QC 엔지니어로서, **고객 출고용 엑셀 G열이 QC 결과와 일치하는지 최종 검수하고 승인한 보정만 자동 기입**받고 싶다 (🟡 v1.6 진행).

**QC 팀 리드 관점**
- 팀 리드로서, 모든 엔지니어가 **동일한 최신 Spec**을 사용하기를 원한다 (✅ v1.2).
- 팀 리드로서, Spec 변경 시 EXE 재배포 없이 **실시간 반영**되기를 원한다 (✅ v1.2).
- 팀 리드로서, 신규 프로필 생성 시 **자료구조 일관성**이 보장되기를 원한다 (✅ v1.4 모듈 일괄 임포트).
- 팀 리드로서, 외부 보고용 리포트를 **회사 브랜딩**에 맞게 커스터마이징하고 싶다 (✅ v1.5).
- 팀 리드로서, 보안 패치를 **강제 업데이트**로 전사에 즉시 반영하고 싶다 (✅ v1.5).
- 팀 리드로서, 장비별·기간별 **QC 통과율 트렌드**를 보고 싶다 (v2.0+).

**관리자 관점 (Spec 편집)**
- Spec 관리자로서, Common Base를 편집하여 모든 장비 프로파일에 공통 스펙을 상속시키기를 원한다 (✅ v1.1 + v1.3 Admin 통합).

---

## 8. Requirements

### 8.1 Must-Have (P0) — v1.0~v1.1 완료, 유지 필수

| ID | 요구사항 | 상태 | 수용 기준 |
|----|---------|------|-----------|
| R1 | XML DB 자동 파싱 | ✅ 완료 (v1.0) | Module/Part/Item 계층 정확 추출 |
| R2 | Range/Exact/Check 3종 검증 | ✅ 완료 (v1.0) | 경계값 포함/제외 처리 정확 |
| R3 | Common Base 상속 프로파일 | ✅ 완료 (v1.0) | 오버라이드 시 Base 우선순위 역전 확인 |
| R4 | Excel 3-시트 리포트 생성 | ✅ 완료 (v1.0) | Summary/All/Failed 색상 구분 |
| R5 | N/A(누락 항목) 감지 및 리뷰 | ✅ 완료 (v1.1) | QC 실행 후 자동 다이얼로그 |
| R6 | 관리자 비밀번호 보호 | ✅ 완료 (v1.0~v1.3) | Profile/Base 편집 시 인증 |
| R7 | 원본 DB 읽기전용 접근 | ✅ 완료 (v1.0) | 파일 수정 불가 |

### 8.2 Must-Have (P0) — v1.2 (Server DB Sync) — ✅ 완료

| ID | 요구사항 | 상태 | 수용 기준 |
|----|---------|------|-----------|
| R8 | PostgreSQL 직접 연결 (psycopg2) | ✅ 완료 | REST API 없이 직결, `connect_timeout=5` |
| R9 | 서버 → 로컬 JSON 캐시 동기화 | ✅ 완료 | `SyncManager`가 주기/수동 갱신 |
| R10 | 오프라인 폴백 | ✅ 완료 | 서버 불통 시 로컬 캐시로 정상 동작 |
| R11 | 앱 내 서버 접속 설정 UI | ✅ 완료 | Host/Port/DB/계정, **자격증명 Fernet 암호화 저장** |
| R12 | SpecManager 인터페이스 무변경 | ✅ 완료 | 기존 로컬 JSON 읽기 로직 그대로 재사용 |

> 서버 인프라: 사내 Docker Compose 스택 (PostgreSQL 5434 / pgAdmin 5050 / 운영 중)

### 8.3 P0/P1 — v1.3~v1.5 — ✅ 완료

| ID | 요구사항 | 버전 | 상태 |
|----|---------|------|------|
| R13 | 관리자 모드 통합 (Admin 단일 진입점) | v1.3 | ✅ 완료 — `pqc123` 인증, 서버 설정 + Spec 관리 + 리포트 템플릿 통합 |
| R14 | DB STRUCTURE 검색 + 매치 네비게이션 | v1.4, v1.5 | ✅ 완료 — 250ms 디바운스, F3/Shift+F3, ▲/▼ 버튼 |
| R15 | 모듈 일괄 임포트 (DB/Base/Profile) | v1.4 | ✅ 완료 — 3가지 충돌 전략 (Skip/Update/Abort) |
| R16 | Profile Viewer 결과 필터 (All/Pass/Check/Fail) | v1.4 | ✅ 완료 |
| R17 | Open DB 서버 폴더 접근 보강 | v1.5 | ✅ 완료 — 마지막 경로 기억, 4상태 안내, 깊이 제한 재귀 |
| R18 | 자동 업데이트 체크 (PG `app_releases`) | v1.5 | ✅ 완료 — 일반/강제 모드, EXE 자동 교체 X |
| R19 | Excel 리포트 템플릿 커스터마이징 | v1.5 | ✅ 완료 — 회사 정보, placeholder, Cover Page |

### 8.4 Must-Have (P0) — v1.6 (Final Checklist QC / Approved Auto-Fill) — 🟡 진행 중

> **현황 (2026-04-29 기준)**: Final Checklist QC 핵심 엔진, 검수자 UI, 승인 UX, Profile Coverage, 언어 전환, 독립 창, checklist 전용 경로, Spec/Profile 검색 보강 구현 완료. 단위·회귀 테스트 `182 passed, 6 skipped` 기준으로 통과. 남은 핵심 작업은 실제 현장 checklist 샘플 검증과 배포 빌드 확인이다.

| ID | 요구사항 | 상태 | 수용 기준 |
|----|---------|------|-----------|
| R20 | 5단 캐스케이드 매핑 파이프라인 | 🟡 진행 중 | explicit → learned → exact → fuzzy(rapidfuzz) → unit_hint |
| R21 | 학습 매핑 사전 (서버 PG + 로컬 캐시) | 🟡 진행 중 | `checklist_mappings` 테이블 + 모델별 JSON 캐시 |
| R22 | 승인 행만 결과 사본에 기입 + 안전 가드 | 🟡 진행 중 | 원본 보존, 내부 사본 생성, G열 QC 값, M열 DB_Key 옵션 기본 ON, `_AutoFill_Log` 시트 |
| R23 | 검수자 UI 다이얼로그 | 🟡 진행 중 | Preflight, 위험도, Profile Coverage, 필터, 승인 체크, 예외 설정, 셀/DB_Key 복사 |
| R24 | 독립 창 + checklist 경로 분리 | 🟡 진행 중 | 메인창 비차단, 마지막 checklist 폴더 기억, Maximize/Restore |

### 8.5 Nice-to-Have (P1) — v1.7+

| ID | 요구사항 | 설명 |
|----|---------|------|
| R25 | 다국어(한/영) 확대 | Final Checklist QC 외 Admin/Main UI까지 단계적 확대 |
| R26 | Item Detail Dialog | 항목 더블클릭 시 히스토리/설명 표시 |
| R27 | 여러 DB 동시 비교 | 장비 간 Spec 편차 분석 |
| R28 | PDF 리포트 옵션 | 외부 보고용 |
| R29 | LLM 기반 매핑 후보 추천 (v1.6 확장) | 매핑 사전 학습 가속 (사내 정책 후 결정) |
| R30 | 고객 전달용 Clean Copy Export | 내부 DB_Key가 포함된 마스터 사본에서 고객 전달본을 분리 |

### 8.6 Future Considerations (P2) — v2.0+

| ID | 요구사항 | 설명 |
|----|---------|------|
| R31 | QC 히스토리 저장 (서버) | 모든 검사 결과를 DB에 누적 저장 |
| R32 | 통계 대시보드 (Web) | 팀 리드용 품질 트렌드 시각화 |
| R33 | 자동 백업 시스템 | 프로파일·결과 스냅샷 |
| R34 | 감사 로그 (Audit Trail) | 누가 언제 Spec/매핑 변경했는지 추적 |
| R35 | 역할 기반 권한(RBAC) | 엔지니어/리드/관리자 권한 분리 |

---

## 9. Technical Architecture (요약)

### 9.1 v1.5.1 현재 상태
```
[사내 PostgreSQL :5434] ─(psycopg2)─→ SyncManager ─→ 로컬 JSON 캐시
                                                          ↓
                                            SpecManager (인터페이스 동일)
                                                          ↓
[DB Folder(XML)] → XMLParser → DBExtractor → QCComparator
                                                  ↓
                                  ChecklistValidator → ExcelReportGenerator (템플릿 적용)
                                                  ↓
                                          Admin Window (서버 / Spec / 리포트 템플릿)
                                                  ↓
                                          UpdateChecker (app_releases)
```

### 9.2 v1.6 목표 (Final Checklist QC)
```
QCComparator (qc_report)
    ↓
ChecklistFinalQcEngine.analyze
    ↓
FinalChecklistQcDialog (Preflight / Profile Coverage / Approval)
    ↓                                       ↘
ChecklistFinalQcEngine.apply_approved       SyncManager (checklist_mappings)
    ↓
[내부 결과 사본] + G열 QC 값 + M열 DB_Key + _AutoFill_Log 시트
```

**설계 원칙**: Spec 저장소·검증 엔진·자동기입 엔진이 인터페이스로 격리됨 — 변경 영향 최소화.

---

## 10. Roadmap

| 버전 | 시기 | 테마 | 핵심 내용 |
|------|------|------|----------|
| **v1.0.0** | 2025-12-26 ✅ | 초기 릴리즈 | 로컬 XML QC 엔진, Excel 리포트 |
| **v1.1.0** | 2026-03-11 ✅ | Profile 고도화 | Common Base 편집, N/A 리뷰, Multi-file 구조 |
| **v1.2.x** | 2026-04 ✅ | Server DB Sync | PostgreSQL 직결, 오프라인 폴백, 접속 UI |
| **v1.3.0** | 2026-04-21 ✅ | 관리자 통합 | Admin 단일 진입점 (서버 + Spec + 템플릿) |
| **v1.4.0** | 2026-04-21 ✅ | 사용성 강화 | DB 검색, 모듈 일괄 임포트, 결과 필터 |
| **v1.5.0~5.2** | 2026-04-27 ✅ | 검색 네비/자동업데이트/템플릿 | 매치 Prev/Next, app_releases, 리포트 템플릿, 사내 매핑드라이브 핫픽스 |
| **v1.6.0** | **2026-Q2 (진행 중)** | **Final Checklist QC** | 최종 검수, 승인 행 자동기입, Profile Coverage, 한/영 전환, 독립 창 |
| v1.7.0 | 2026-Q3 | 사용성·국제화 | 다국어 확대, 아이템 상세, Clean Copy Export |
| v1.8.0 | 2026-Q4 | 비교·분석 | 멀티 DB 비교, PDF 리포트 |
| v2.0.0 | 2027+ | **QC 플랫폼** | 히스토리 서버 저장, 웹 대시보드, RBAC, 감사로그 |

---

## 11. Success Metrics

### 11.1 Leading Indicators (단기, 출시 후 1~3개월)

| 지표 | 정의 | 목표 | 실측 (v1.5.1) |
|------|------|------|---------------|
| 채택률 | QC 엔지니어 중 주 1회 이상 사용자 비율 | 90% 이상 | 측정 중 |
| 장비당 QC 소요시간 | 로드~리포트 생성 평균 시간 | ≤ 15 분 | ✅ 10~15분 달성 |
| Spec 반영 리드타임 | 관리자 Spec 변경 → 엔지니어 반영까지 | ≤ 1 시간 | ✅ 즉시 (v1.2) |
| N/A 항목 조기 감지율 | 출하 전 누락 감지 건수 / 전체 누락 | ≥ 95% | 측정 중 |
| 출고 엑셀 승인 보정 비율 (v1.6) | Final QC에서 승인되어 사본에 반영된 G열 셀 / 보정 필요 셀 | ≥ 90% (학습 사전 누적 후) | v1.6 출시 후 측정 |

### 11.2 Lagging Indicators (중장기, 3~12개월)

| 지표 | 목표 |
|------|------|
| 출하 후 DB 설정 관련 **필드 이슈 건수** | 전년 대비 **50% 감소** |
| QC 엔지니어 **월간 공수(시간)** | 전년 대비 **40% 감소** → v1.6 후 **50% 감소 목표** |
| 출고 Checklist **재발행 건수** (오기입 사유) | v1.6 후 **80% 감소** |
| 내부 사용자 만족도 (사내 설문) | **4.0 / 5.0 이상** |

---

## 12. Risks & Mitigations

| # | 리스크 | 영향 | 대응 |
|---|--------|------|------|
| 1 | 사내 PostgreSQL 서버 장애 | QC 중단 | **오프라인 폴백** (R10) — 로컬 JSON 캐시로 정상 동작 ✅ |
| 2 | 서버 접속 정보 유출 | 보안 사고 | 앱 내 **Fernet 암호화 저장**, 관리자 비밀번호 보호 ✅ |
| 3 | Spec/매핑 변경 누락·실수 | 오판정 리스크 | v2.0 감사로그(R34) 및 RBAC(R35)로 통제 |
| 4 | 단일 개발자 의존 (Bus factor) | 유지보수 중단 | 문서화 강화(PRD/CHANGELOG/SKILL), 코드 리뷰어 확보 필요 |
| 5 | CustomTkinter 생태계 한계 | UI 확장성 제약 | v2.0 웹 대시보드로 UI 분리 검토 |
| 6 | DB 포맷 변경(XE Service 업데이트) | 파서 호환성 | Parser 추상화, 회귀 테스트 정비 (현재 182 passed, 6 skipped) |
| 7 | 사내 NPFS DRM 환경 매핑드라이브 차단 | 서버 폴더 미접근 | **별도 SMB 서버 사용** (UNC `\\10.60.20.11\...`) — v1.5.2에서 운영 가이드 추가 ✅ |
| 8 | v1.6 Final QC 매핑/커버리지 정확도 저조 | 자동화 효과 미흡 | learned mapping + Profile Coverage + Missing in Checklist 진단 + 승인 행만 적용 |
| 9 | v1.6 출고 엑셀 수식 손상 | 고객 전달 문서 손상 | 원본 보존, 내부 사본 생성, formula/group/protected/표지 시트 차단, openpyxl `data_only=False` 로딩 |

---

## 13. Timeline & Milestones

### 13.1 v1.2~v1.5 — ✅ 완료 (2026-04 마감)
| 단계 | 산출물 | 상태 |
|------|--------|------|
| v1.2 Phase 1~6 | PG 스키마, SyncManager, 접속 UI, 폴백 QA, 파일럿, 정식 배포 | ✅ 완료 |
| v1.3 | Admin 통합, 비밀번호 인증, _deprecated 격리 | ✅ 완료 |
| v1.4 | 검색, 모듈 임포트, 결과 필터 | ✅ 완료 |
| v1.5.0 | 검색 네비, 서버 폴더 보강, 자동 업데이트, 리포트 템플릿 | ✅ 완료 |
| v1.5.1~5.2 | 사내 매핑드라이브 핫픽스, NPFS DRM 운영 가이드 | ✅ 완료 |

### 13.2 v1.6 — 🟡 진행 중
| 단계 | 산출물 | 상태 | 비고 |
|------|--------|------|------|
| Phase 1. 서버 스키마 + Sync | `checklist_mappings` 테이블, ServerDBManager CRUD, SyncManager 확장 | ✅ 완료 | 서버 PG 마이그레이션 완료 (2026-04-28) |
| Phase 2. 매핑 파이프라인 | text_normalizer + checklist_mapper (5단 캐스케이드) | ✅ 완료 | rapidfuzz hidden import 등록 |
| Phase 3. Final QC 엔진 | 읽기 전용 분석, 승인 행 적용, 원본 보존, `_AutoFill_Log` | ✅ 완료 | |
| Phase 4. 검수자 UI | Final Checklist QC 다이얼로그 + main_window 진입점 | ✅ 완료 | 한/영 전환, 필터, 승인 UX |
| Phase 5. 사용성 보강 | Profile Coverage, 셀/DB_Key 복사, modeless 창, Maximize/Restore, checklist 경로 분리 | ✅ 완료 | |
| Phase 6. 테스트 | 단위/통합/회귀 테스트 182 passed, 6 skipped | ✅ 완료 | 2026-04-29 기준 |
| Phase 7. PyInstaller 빌드 검증 | EXE 동작 + rapidfuzz/openpyxl 검증 | ⚪ 대기 | 사용자 환경 별도 |
| Phase 8. 현장 샘플 파일럿 + 정식 배포 | 실제 checklist 2~3개 검증 → 전사 | ⚪ 대기 | |

**총 예상 기간**: 빌드/파일럿 1~2주 + 정식 배포

---

## 14. Open Questions

| # | 질문 | 담당 |
|---|------|------|
| Q1 | 사내 PostgreSQL의 **백업/고가용성 정책** 확정 필요 | Infra / 경영진 |
| Q2 | Spec 편집 권한을 **리드 1인 독점** vs **다수 관리자**로 할지 | QC 팀 리드 |
| Q3 | v1.6 파일럿 대상 엔지니어 선정 및 Beta 기간 | QC 팀 리드 |
| Q4 | v2.0 웹 대시보드는 **사내 웹서버 vs 별도 앱**으로 구축할지 | 경영진 / Infra |
| Q5 | 해외법인 사용 시 **네트워크 지연** 대응 방안 | Infra |
| Q6 | 다국어 우선순위 (한/영 외 추가 언어 필요 여부) | 경영진 |
| Q7 | v1.6 결과 사본을 내부 마스터로 고정할지, 고객 전달 가능 파일로도 볼지 정책 확정 필요 | QC 팀 리드 |
| Q8 | LLM 기반 매핑 후보 추천(R29) — 사내 LLM 사용 가능 여부 | Infra / 보안 |

---

## 15. Resource & Investment

| 항목 | v1.0~v1.5까지 | v1.6 추가 | v2.0 예상 |
|------|---------------|-----------|-----------|
| 개발 인력 | 1명 (Levi.Beak, 사이드) | 동일 | 2~3명 (웹 대시보드 별도) |
| 인프라 | 엔지니어 PC + 사내 PG (5434) + pgAdmin (5050) | `checklist_mappings` 테이블 추가 (DDL만) | 웹 호스팅, 히스토리 DB 확장 |
| 라이선스 비용 | 없음 (OSS) | 없음 (rapidfuzz MIT) | 없음 또는 클라우드 호스팅 비용 |
| 외부 의존 | 없음 | 없음 | 사내 LLM 평가 시 |

**투자 관점**: v1.0~v1.6은 추가 라이선스/인프라 비용 **최소**. v2.0부터 웹 대시보드 호스팅 검토 필요.

---

## 16. Appendix

### A. 용어 정리
- **QC**: Quality Control (품질 검사)
- **Spec**: 항목별 기준값 정의(Range/Exact/Check)
- **Common Base**: 모든 장비 프로파일이 상속하는 공통 Spec
- **Equipment Profile**: 특정 장비 모델별 Spec (Common Base를 오버라이드)
- **N/A Item**: 프로파일에는 있으나 DB에 존재하지 않는 항목
- **DB_Key**: `Module.PartType.PartName.ItemName` dot-notation 키 (Excel M열 ↔ QC 결과 lookup)
- **Final Checklist QC**: 완성 checklist를 QC 결과와 비교해 누락/불일치/미매핑/보호 행을 최종 검수하는 v1.6 기능
- **Approved Auto-Fill**: 검수자가 승인한 `Missing/Mismatch` 행만 내부 결과 사본의 G열/M열에 기입하는 방식
- **Profile Coverage**: 현재 profile의 Spec 항목이 checklist에 DB_Key로 얼마나 포함됐는지 확인하는 진단 지표
- **NPFS DRM**: 사내 보안망 매핑 드라이브의 커널 미니필터 차단 환경 (v1.5.2 운영 가이드 참조)

### B. 관련 문서
- [README.md](README.md)
- [CHANGELOG.md](CHANGELOG.md)
- [사용설명서.md](사용설명서.md)
- [final_checklist_qc_verification.md](final_checklist_qc_verification.md)
- 내부 계획 문서: `.cwm/docs/plans/` (260413~260428)

### C. 변경 이력
| 버전 | 일자 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 1.0 | 2026-04-21 | 초안 작성 (v1.1.0 기준, 경영진 보고용) | Levi.Beak |
| 1.1 | 2026-04-21 | v1.2 Server DB Sync 상태를 "진행 중"으로 업데이트 | Levi.Beak |
| **2.0** | **2026-04-28** | **v1.2~v1.5.1 완료 반영, v1.6 초기 자동기입 진행 상태 추가, 파일명 v1.1.0 제거 (영구 사용)** | **Levi.Beak** |
| **2.1** | **2026-04-29** | **v1.6 Final Checklist QC, 승인 UX, Profile Coverage, 독립 창, Spec/Profile 검색 보강 반영** | **Levi.Beak** |

---

*Copyright © 2026 Park Systems. Internal use only.*
