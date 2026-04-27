# 변경 이력 (CHANGELOG)

DB_Compare QC 검사 도구의 모든 주요 변경사항을 기록합니다.

형식: [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/)  
버전 관리: [Semantic Versioning](https://semver.org/lang/ko/)

---

## [1.4.0] - 2026-04-21

### 사용성 강화 — 검색 / 임포트 / 결과 필터 🔍

### 추가됨 (Added)

#### F1. DB STRUCTURE 검색
- ✅ 메인 창의 DB 트리 헤더에 **검색 입력창** 추가 (`src/ui/main_window.py`)
- ✅ 250ms 디바운스 + 실시간 검색 (Enter 키는 즉시 실행, ESC로 클리어)
- ✅ 매칭 시 **자동 펼침 + 하이라이트(노랑) + 첫 매치로 스크롤**
- ✅ 검색어 클리어 시 **검색 시작 전 expand/collapse 상태 복원**
- ✅ 매치 카운트 라벨 (`"N matches"` 녹색 / `"0 matches"` 주황)
- ✅ DB 미로드 상태에서는 검색 입력창 자동 비활성

#### F2. Admin Spec 관리 — 모듈 일괄 임포트
- ✅ Spec 관리 탭에 **"+ 임포트" 버튼** 추가 (`src/ui/server_spec_manager.py`)
- ✅ **3가지 소스** 지원 (한 다이얼로그에서 라디오 전환):
  - **DB 폴더 (XML)** — `DBExtractor`로 자료구조 자동 추출
  - **Common Base** — 현재 Common Base 전체 가져오기
  - **다른 Equipment Profile** — 자기 자신은 자동 제외
- ✅ 트리 + 체크박스 UI, **기존 항목 골드(#c9a33e)로 시각 구분**
- ✅ 실시간 검색 필터 + "모두 선택/해제" 헬퍼 버튼
- ✅ **충돌 처리 3가지 전략** (라디오):
  - **Skip (기본)** — 기존 항목 보존, 신규만 추가
  - **Update** — 기존 항목 Spec을 소스 값으로 덮어쓰기
  - **Abort** — 충돌 발생 시 트랜잭션 전체 롤백
- ✅ 신규 메서드 `ServerDBManager.bulk_add_specs(profile_id, items, conflict_strategy)` — 단일 트랜잭션, `bump_version` 1회만 호출
- ✅ `read_only` 모드(오프라인)에서 "+ 임포트" 버튼 자동 비활성

#### F3. Profile Viewer 결과 필터
- ✅ Profile Viewer 헤더에 **Segmented Button** `[ All | Pass | Check | Fail ]` 추가
- ✅ QC 실행 후 **Pass/Check/Fail만 분리 보기** 가능
- ✅ 카운트 라벨 동적 갱신 (`"(12 of 156 items, FAIL)"` + 상태별 색상)
- ✅ 프로필 변경 시 **필터 자동 All로 리셋**
- ✅ QC 미실행 상태에서 Pass/Check/Fail 클릭 시 **상태바 안내 메시지**
- ✅ 필터 전환 시 **선택 항목(DB_Key) 보존** (가능한 경우)

### 수정됨 (Changed)
- 🎨 앱 타이틀 `v1.3.0` → `v1.4.0`
- 🔧 `update_profile_viewer_with_results` 끝에 캐시 빌드 + 현재 필터 자동 재적용

### 근거
- 2,600+ 항목 DB에서 수동 스크롤 비효율 → F1 검색
- 신규 프로필 작성 시 자료구조 일관성 위험 (수기 입력 오타·구조 불일치) → F2 일괄 임포트
- QC 결과 검토 시 Fail 항목만 빠르게 보고 싶음 → F3 분리 필터

PRD §11 "장비당 QC 소요시간 ≤15분" 목표 달성에 기여, "Spec 표준화" 전략 목표(§4) 강화.

---

## [1.0.0] - 2025-12-26

### 최초 릴리즈 🎉
DB_Compare QC 검사 도구의 첫 번째 공식 버전

### 추가됨 (Added)
#### 핵심 기능
- ✅ XML 기반 DB 파싱 시스템 (Module, Part, Item 계층 구조)
- ✅ QC 프로필 관리 시스템 (상속 지원)
- ✅ 자동 QC 비교 엔진 (Range/Exact 검증)
- ✅ Excel 리포트 생성 (3-시트 형식)
- ✅ JSON 리포트 Export 옵션

#### UI 컴포넌트
- ✅ CustomTkinter 기반 메인 윈도우 (1600x800)
- ✅ 계층형 DB 트리 뷰 (컬러 코딩)
- ✅ QC 결과 패널 (컴팩트 그리드 레이아웃)
- ✅ 프로필 뷰어 (실시간 결과 표시)
- ✅ Dark/Light 테마 지원

#### 프로필 관리
- ✅ 듀얼 뷰 모드 (Table ↔ Tree 전환)
- ✅ 실시간 검색 및 필터링
- ✅ 프로필 CRUD 작업 (Create, Read, Update, Delete)
- ✅ 비밀번호 보호 (pqclevi)
- ✅ 상속 기반 프로필 시스템

#### 고급 기능
- ✅ Expand All / Collapse All 트리 컨트롤
- ✅ 항목 카운트 표시
- ✅ 실시간 상태 업데이트
- ✅ 자동 timestamp 생성
- ✅ 오류 처리 및 로깅

### 수정됨 (Changed)
#### UI/UX 개선
- 🎨 윈도우 크기 최적화: 1200x800 → **1600x800**
- 🎨 패널 비율 조정: Left 540px, Right 1060px
- 🎨 폰트 크기 향상: 전체 14-18pt로 증가
- 🎨 QC Results 재디자인: 컴팩트 2-컬럼 그리드
- 🎨 Spec 컬럼 축소: 150px → 90px (가로 스크롤 제거)

#### 성능 개선
- ⚡ DB 로깅 최적화: INFO → DEBUG (반복 로그)
- ⚡ 트리 뷰 렌더링 최적화
- ⚡ 메모리 사용량 개선

### 수정된 버그 (Fixed)
#### 크리티컬 버그
- 🐛 파일 인코딩 오류 (한글/이모티콘 손상) → UTF-8로 완전 재작성
- 🐛 DB 로딩 실패 (`extract_all` → `build_hierarchy` 메서드명 수정)
- 🐛 Profile Manager import 오류 → 정확한 클래스명 사용
- 🐛 Export 기능 오류 → 클래스/메서드명 수정, timestamp 안전 처리
- 🐛 Invalid default profile (NX10_Standard) → settings.json 정리

#### UI 버그
- 🐛 Expand/Collapse 버튼 비활성 → 메서드 구현 완료
- 🐛 Profile Viewer 가로 스크롤 → 패널 너비 조정
- 🐛 QC Results 세로 스크롤 → 컴팩트 레이아웃으로 재설계
- 🐛 Item count 미표시 → 동적 카운트 로직 추가

#### 안정성 개선
- 🛡️ 안전한 timestamp 처리 (fallback to current time)
- 🛡️ Open DB 예외 처리 강화
- 🛡️ 파일 다이얼로그 오류 포착
- 🛡️ JSON 로딩 오류 처리

### 제거됨 (Removed)
- ❌ "Create new profile" 프롬프트 (워크플로우 간소화)
- ❌ "Tools" 메뉴 (사용하지 않음)
- ❌ Tree View 편집 모드 (Profile Manager로 통합)
- ❌ 모든 한글 UI 텍스트 (영문으로 대체, 인코딩 문제 방지)
- ❌ 모든 이모티콘 (안정성 향상)

### 보안 (Security)
- 🔒 Profile Manager 비밀번호 보호 추가
- 🔒 비밀번호 변경: parksystems2025 → **pqclevi**
- 🔒 읽기 전용 DB 접근 (원본 수정 방지)

### 문서화 (Documentation)
- 📖 README.md (한국어, 종합 가이드)
- 📖 사용설명서.md (한국어, 단계별 튜토리얼)
- 📖 requirements.txt (패키지 목록)
- 📖 walkthrough.md (개발 세션 기록)
- 📖 task.md (작업 체크리스트, 98% 완료)

---

## [1.3.0] - 2026-04-21

### 관리자 모드 통합 🔒

### 추가됨 (Added)
- ✅ **AdminWindow 신규** (`src/ui/admin_window.py`) — 서버 설정 + Spec 관리를 단일 비밀번호 보호 창으로 통합
- ✅ 메인 툴바에 **🔒 Admin 버튼** 추가 (`pqc123` 인증)
- ✅ Spec 관리 탭에 **오프라인 읽기 전용 모드** — 오프라인 시 편집 버튼 비활성화 + 배너 표시
- ✅ `src/utils/config_helper.py`에 `ADMIN_PASSWORD` 상수 분리

### 수정됨 (Changed)
- 🔧 `ServerSettingsDialog` → `ServerSettingsPanel` (`CTkFrame` 기반 임베더블 패널)
- 🔧 `ServerSpecManagerWindow` → `ServerSpecManagerPanel` (`CTkFrame` 기반, read-only 지원)
- 🎨 Online/Offline 인디케이터 포맷 통일 (`● Online` / `● Offline`)
- 🎨 앱 타이틀 `v1.0.0` → `v1.3.0`

### 제거됨 (Removed)
- ❌ 메인 툴바의 **Profile Manager 버튼** (Admin → Spec 관리로 이관)
- ❌ 메인 툴바의 **Server DB 버튼** (Admin → Spec 관리로 이관)
- ❌ 메인 툴바의 **Server 설정 버튼** (Admin → 서버 설정으로 이관)
- ❌ `src/ui/profile_manager.py` → `src/ui/_deprecated/`로 이동
- ❌ `src/ui/profile_editor.py` → `src/ui/_deprecated/`로 이동

### 보안 (Security)
- 🔒 서버 접속·Spec 편집 진입을 비밀번호 인증(`pqc123`)으로 일원화
- 🔒 생산 엔지니어의 우발적 서버 설정 변경·Spec 수정 방지

### 근거
- **Single Source of Truth** 원칙 강화: Profile Manager(로컬)와 Server DB(서버)의 중복 편집 경로 제거
- 역할 분리: 생산 엔지니어(조회·QC 실행) vs Spec 관리자(편집)의 UI 수준 권한 분리
- PRD §8.4 R21/R22(감사로그·RBAC)의 첫 단계

---

## [1.1.0] - 2026-03-11

### Profile Manager & Editor 개선 🔧

### 추가됨 (Added)
#### Add Items from DB 다이얼로그
- ✅ 기존 항목 / 새 항목 시각적 구분 (기존=amber-gold ☑, 새=일반 ☐)
- ✅ 기존 항목 토글 불가 (오클릭 무시)
- ✅ 실시간 검색/필터 기능 (Module, Part, Item 이름 검색)
- ✅ 다이얼로그 크기 1000×700으로 확대 (Profile Editor 동일)
- ✅ 하단 카운트: `Selected: N new | M existing` 표시
- ✅ Module/Part 노드에 `(N parts)` / `(선택/총 items)` 카운트 표시
- ✅ 항목 선택 시 Part 노드 카운트 실시간 업데이트

#### Common Base 편집
- ✅ Profile Manager에서 Common Base 직접 편집 가능
- ✅ ★ Common Base Editor 전용 UI 모드
- ✅ 비밀번호 인증 (`pqclevi`) 후 편집 진입
- ✅ `common_base.json`에 직접 저장

#### N/A Items Review Dialog
- ✅ DB에 누락된 항목(N/A)을 별도 다이얼로그로 리뷰
- ✅ QC 실행 후 누락 항목 자동 감지 및 알림

#### Multi-file Config 구조
- ✅ `config/common_base.json` — Common Base 스펙
- ✅ `config/profiles/*.json` — 개별 장비 프로파일
- ✅ 상속 기반 프로파일 시스템 (Common_Base ← Equipment Profile)

### 수정됨 (Changed)
- 🎨 Profile Editor 모든 트리뷰에 `(N parts)` / `(N items)` 카운트 표시
- 🎨 Dark Mode에서 기존 항목 amber-gold 하이라이트

### 수정된 버그 (Fixed)
- 🐛 Profile Manager 우클릭 삭제 시 `save_spec_file()` 레거시 호출 → `save_equipment_profile()` 교체
- 🐛 Profile Manager 더블클릭 편집 시 같은 레거시 저장 버그 수정
- 🐛 Common Base Edit 시 `simpledialog` import 누락 → 추가
- 🐛 Comparator N/A 감지 로직 개선

### 보안 (Security)
- 🔒 Common Base 편집 시 관리자 비밀번호 필수 입력

---

## [향후 계획] - Unreleased

### 예정 (Planned)
- [ ] PyInstaller로 독립 실행 파일(.exe) 생성
- [ ] 프로그램 아이콘 추가
- [ ] 설치 프로그램 (Installer) 제작
- [ ] 다국어 지원 (영어/한국어)
- [ ] Item Detail Dialog (더블클릭 시 상세 정보)

### 고려 중 (Considering)
- [ ] 여러 DB 동시 비교 기능
- [ ] 히스토리 기능 (과거 QC 결과 추적)
- [ ] 자동 백업 시스템
- [ ] 네트워크 경로 지원 개선
- [ ] PDF 리포트 생성
- [ ] 통계 대시보드

---

## 버전 번호 정책

형식: `MAJOR.MINOR.PATCH`

- **MAJOR**: 호환성이 깨지는 큰 변경
- **MINOR**: 하위 호환성을 유지하는 기능 추가
- **PATCH**: 버그 수정 및 작은 개선

예:
- `1.0.0`: 최초 릴리즈
- `1.0.1`: 버그 수정
- `1.1.0`: 새 기능 추가
- `2.0.0`: 대규모 리팩토링

---

## 주요 마일스톤

| 날짜 | 마일스톤 | 설명 |
|------|----------|------|
| 2025-12-22 | 개발 시작 | 프로젝트 기획 및 구조 설계 |
| 2025-12-23 | 코어 엔진 완성 | XML Parser, DB Extractor, Comparator |
| 2025-12-24 | GUI 개발 | Main Window, Tree View, Results Panel |
| 2025-12-25 | 프로필 관리 | Profile Manager, Editor, Dual-View |
| 2025-12-26 | UI 최적화 & 버그 수정 | 최종 polish 및 안정화 |
| 2025-12-26 | v1.0.0 릴리즈 🎉 | 첫 번째 공식 버전 |

---

## 기여자 (Contributors)

**Lead Developer**: Levi.Beak (levi.beak@parksystems.com)  
**Organization**: Park Systems - XE Service Quality Control Team  
**Project Duration**: 2025-12-22 ~ 2025-12-26 (5 days)

---

## 라이선스

Copyright © 2025 Park Systems. All rights reserved.  
Internal use only. External distribution prohibited.

---

**최종 업데이트**: 2025-12-26  
**문서 버전**: 1.0
