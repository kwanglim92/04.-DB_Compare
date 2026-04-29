# DB_Manager — QC Inspection Tool

![Version](https://img.shields.io/badge/version-1.5.1-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-Internal-red)

Park Systems XE Service DB의 QC(Quality Control) 검사를 자동화하는 사내 전용 데스크톱 도구입니다. v1.0~v1.5.1까지 4개월간 진화하여 단순 검증 도구에서 **서버 동기화 + 검색·임포트 + 자동 업데이트 + 리포트 템플릿 + 출고 문서 자동 기입(v1.6 진행)** 까지 포괄하는 QC 운영 도구로 자리잡았습니다.

---

## 🚀 빠른 시작 (3단계)

1. **EXE 실행** — 사내 공유 위치의 `DB_Compare_QC_Tool.exe` 더블클릭
2. **Open DB** → 프로필 선택 → **Run QC** → **Export**
3. (v1.6 이후) **Auto-Fill Checklist** 버튼으로 출고용 엑셀 자동 기입

상세한 단계별 가이드는 **[사용설명서.md](사용설명서.md)** 를 참조하세요.

---

## ✨ 주요 기능 (v1.5.1 기준)

| 영역 | 기능 |
|------|------|
| **QC 엔진** | XML 자동 파싱, Range/Exact/Check 3종 검증, N/A 누락 감지 |
| **프로필 관리** | Common Base 상속, 모듈 일괄 임포트, 듀얼 뷰(Table/Tree) |
| **서버 동기화** | PostgreSQL 직결 + 로컬 JSON 캐시 폴백, 오프라인 정상 동작 |
| **사용성** | DB 트리 검색(F3/F4 네비), 결과 필터(All/Pass/Check/Fail) |
| **자동 업데이트** | PG `app_releases` 기반, 강제/일반 모드 |
| **리포트** | Excel 3-시트 (Summary / All / Failed) + 회사 브랜딩 템플릿 |
| **관리자 모드** | 단일 비밀번호로 서버 설정 + Spec 관리 + 리포트 템플릿 통합 |
| **출고 문서 자동 기입** (v1.6 진행) | Industrial Checklist G열 5단 매핑 + 안전 가드 |

---

## 💻 시스템 요구사항

| 항목 | 사양 |
|------|------|
| OS | Windows 10 이상 |
| Python | 3.11+ (개발/소스 실행 시) |
| 해상도 | 1600x800 이상 권장 |
| 사내 PG | PostgreSQL 5434 / pgAdmin 5050 (서버 동기화 시) |

### 의존 라이브러리
```
customtkinter >= 5.2.1
openpyxl >= 3.1.2
psycopg2-binary >= 2.9
cryptography >= 41.0
rapidfuzz >= 3.0  (v1.6+)
```

---

## 📦 설치 (소스 빌드)

```bash
# 1. 패키지 설치
cd "C:\Users\Spare\Desktop\03. Program\04. DB_Compare"
pip install -r requirements.txt

# 2. 실행
python main.py

# 3. EXE 빌드 (선택)
build.bat
# → dist/DB_Compare_QC_Tool.exe 생성
```

---

## 📚 문서 가이드

| 문서 | 대상 | 내용 |
|------|------|------|
| **[사용설명서.md](사용설명서.md)** | 엔드유저 / QC 엔지니어 | 화면별 단계별 사용법, 시나리오, FAQ |
| **[CHANGELOG.md](CHANGELOG.md)** | 모든 사용자 | 버전별 변경 사항 (v1.0~v1.5.2) |
| **[PRD_DB_Manager.md](PRD_DB_Manager.md)** | 경영진 / 사업부 리더 | 제품 요구사항, 로드맵, 성공 지표 |
| **[final_checklist_qc_verification.md](final_checklist_qc_verification.md)** | 검수자 / QC | Final Checklist QC 자동 기입 검증 절차 |

---

## 🔒 보안 / 운영

### 비밀번호
- **`pqc123`** — Admin 창 (서버 설정 + Spec 관리 + 리포트 템플릿) — v1.3+ 통합
- **`pqclevi`** — Common Base 직접 편집 (legacy)

### 데이터 보호
- DB 파일은 읽기 전용으로만 접근 (원본 변경 없음)
- 서버 자격증명은 Fernet 대칭 암호화 저장
- 자동 업데이트는 EXE 자동 교체 X (다운로드 링크만, 사용자 수동 실행)

### 사내 NPFS DRM 환경
일부 매핑 드라이브(`Z:`)가 NPFS 가상 볼륨이면 Python 프로세스가 read 거부됨. 별도 SMB 서버 (`\\10.60.20.11\...`) 사용 권장. 자세한 진단·우회는 [사용설명서.md §7.6](사용설명서.md#76-사내-매핑-드라이브가-동작하지-않을-때-npfs-drm-환경) 참조.

---

## 🛠️ 개발자 정보

| 항목 | 내용 |
|------|------|
| 프로젝트명 | DB_Manager (舊 DB_Compare) |
| 현재 버전 | v1.5.1 (+ v1.5.2 운영 가이드 보강) |
| 다음 버전 | v1.6 — Industrial Checklist Auto-Fill (진행 중) |
| 개발자 | Levi.Beak (levi.beak@parksystems.com) |
| 회사 | Park Systems — XE Service Quality Control Team |

### 기술 스택
- **언어/UI**: Python 3.11+, CustomTkinter
- **데이터**: PostgreSQL 16 (Docker), openpyxl, JSON 캐시
- **퍼지 매칭**: rapidfuzz (v1.6+)
- **빌드**: PyInstaller 단일 EXE + NSIS 설치 프로그램
- **CI/검증**: pytest 147 passed, 3 skipped (현재 v1.5.1 기준선)

---

## 📞 지원

문제 보고 또는 기능 요청: **levi.beak@parksystems.com**

---

## 📄 라이선스

Copyright © 2026 Park Systems. All rights reserved.
**Internal use only — External distribution prohibited.**
