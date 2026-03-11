# DB_Compare - QC 검사 도구

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-Internal-red)

Park Systems XE Service DB의 QC(Quality Control) 검사를 자동화하는 전문 도구입니다.

---

## 📋 목차

- [주요 기능](#주요-기능)
- [시스템 요구사항](#시스템-요구사항)
- [설치 방법](#설치-방법)
- [사용 방법](#사용-방법)
- [검증 타입](#검증-타입)
- [프로필 관리](#프로필-관리)
- [리포트 생성](#리포트-생성)
- [문제 해결](#문제-해결)
- [개발자 정보](#개발자-정보)

---

## 🎯 주요 기능

### 핵심 기능
- ✅ **DB 자동 파싱**: XE Service DB의 XML 구조 완전 분석
- ✅ **QC 프로필 관리**: 장비별 맞춤 검사 기준 설정 및 상속
- ✅ **3가지 검증 타입**: Range, Exact, Check (값 확인만)
- ✅ **유연한 Range 검증**: Min만, Max만, 또는 둘 다 (≥, ≤)
- ✅ **Excel 리포트**: 전문적인 3-시트 리포트 자동 생성
- ✅ **실시간 결과**: 컬러 코딩된 Pass/Fail/Check 트리 뷰

### UI/UX
- 🎨 **Modern UI**: CustomTkinter 기반의 세련된 인터페이스
- 📊 **듀얼 뷰 모드**: Table/Tree 뷰 자유 전환 (프로필 관리자)
- 🔍 **실시간 검색**: 모든 항목에 대한 즉시 필터링
- 📈 **컴팩트 결과**: 스크롤 없이 한눈에 보이는 결과 패널
- 🖥️ **최적화 레이아웃**: 1600x800 해상도에 최적화

---

## 💻 시스템 요구사항

### 필수 사항
- **OS**: Windows 10 이상
- **Python**: 3.11 이상
- **해상도**: 1600x800 이상 권장

### Python 패키지
```
customtkinter >= 5.2.0
openpyxl >= 3.1.0
```

---

## 📦 설치 방법

### 1. Python 설치 확인
```bash
python --version
# Python 3.11 이상이어야 합니다
```

### 2. 패키지 설치
```bash
cd "C:\Users\Spare\Desktop\03. Program\DB_Compare"
pip install -r requirements.txt
```

### 3. 프로그램 실행
```bash
python main.py
```

---

## 🚀 사용 방법

### 기본 워크플로우

#### 1단계: DB 선택
1. 메인 창에서 **"Select DB Folder"** 클릭
2. XE Service DB 폴더 선택 (예: `C:\Park Systems\XEService\DB`)
3. DB 자동 로딩 및 파싱 대기
4. 완료 후 왼쪽 트리 뷰에 DB 구조 표시

#### 2단계: 프로필 선택
1. 상단 **프로필 드롭다운**에서 검사할 프로필 선택
   - 예: `NX-Wafer`, `NX10_Standard` 등
2. 선택 시 하단 "Profile Viewer"에 해당 프로필의 검사 항목 표시

#### 3단계: QC 실행
1. **"Run QC Inspection"** 버튼 클릭 (DB 로딩 완료 시 활성화)
2. 자동으로 모든 항목 검사 수행
3. 결과 확인:
   - 오른쪽 상단: QC 검사 결과 요약
     - Total Items
     - Validated (PASS/FAIL 검증)
     - Checked Only (값만 확인)
     - Pass Rate
   - 왼쪽 트리: 항목별 Pass/Fail/Check 표시 (컬러 코딩)
   - 하단: 프로필 뷰어에 실제 값과 결과 표시

#### 4단계: 리포트 저장
1. **"Export Report"** 버튼 클릭
2. 저장 위치 및 파일명 지정
3. Excel 파일 자동 생성 (3개 시트)
   - Summary: 검사 요약 및 통계
   - All Items: 전체 항목 상세 결과
   - Failed Items: 실패 항목만 필터링

---

## 🔬 검증 타입

### 1. Range (범위 검증)

#### 양쪽 값 지정
```
Min: 70.0, Max: 90.0
→ PASS: 80.0 within [70.0, 90.0]
→ FAIL: 60.0 outside [70.0, 90.0]
```

#### Min만 지정 (이상, ≥)
```
Min: 20.0, Max: (비움)
→ PASS: 25.0 ≥ 20.0
→ FAIL: 15.0 < 20.0
```

#### Max만 지정 (이하, ≤)
```
Min: (비움), Max: 100.0
→ PASS: 80.0 ≤ 100.0
→ FAIL: 120.0 > 100.0
```

### 2. Exact (정확 일치)
```
Expected: "1"
→ PASS: "1" == "1"
→ FAIL: "0" != "1"
```

### 3. Check (값 확인만)
```
PASS/FAIL 판정 없이 값만 기록
→ STATUS: CHECK
→ Message: "Value recorded"
→ 용도: 단순 확인이 필요한 항목
```

---

## 🔧 프로필 관리

### 프로필 관리자 접근
1. 툴바에서 **"Profile Manager"** 버튼 클릭
2. 관리자 비밀번호 입력: `pqclevi`
3. 프로필 관리 창 열림

### 방법 A: Profile Manager (직접 편집)

#### 항목 편집
1. 프로필 선택
2. 항목 **더블클릭**
3. Spec Configuration Dialog:
   - **Range (Min/Max)**: Min, Max 또는 둘 중 하나만
   - **Exact Match**: 정확한 값
   - **Check (Value Only)**: 값만 기록
4. Unit 입력 (선택)
5. Save

#### 항목 삭제
1. 항목 **우클릭**
2. "Delete" 선택
3. 확인 (실제로는 `enabled: false`로 설정)

### 방법 B: Profile Editor (DB 기반 추가)

#### 새 프로필 생성
1. Profile Manager에서 **"New"** 클릭
2. DB 폴더 선택
3. 항목 체크박스 선택
4. 각 항목 더블클릭하여 Spec 설정
5. **"Save Profile"** 클릭 후 이름 입력

#### 기존 프로필 편집
1. 프로필 선택 후 **"Edit"** 클릭
2. DB 폴더 선택
3. 기존 항목 자동 로드 (체크 표시됨)
4. 항목 추가/수정
5. Save (기존 항목과 병합됨)

### 뷰 모드 전환
- **Table View**: 모든 항목을 플랫한 테이블로 표시 (빠른 스캔)
- **Tree View**: 계층 구조로 표시 (Module → Part → Item)
- **Group View** 토글로 자유롭게 전환

### 검색 기능
- 검색창에 키워드 입력
- Module, Part Type, Part, Item 전체에서 검색
- 일치 항목 주황색 강조
- 실시간 필터링

---

## 📊 리포트 생성

### Excel 리포트 구조

#### Sheet 1: Summary (요약)
```
QC Inspection Report

Profile: NX-Wafer
Timestamp: 2025-12-28 19:13:29
DB Root: C:/...
Instrument: nx

Statistics
Total Items:        2,665
Validated Items:    64      (PASS + FAIL)
Checked Only:       2       (CHECK)
✓ Passed:           63
✗ Failed:           1
○ No Spec:          2,596
⚠ Errors:           0

Pass Rate:          98.44%
```

#### Sheet 2: All Items (전체 항목)
- 모든 검사 항목의 상세 결과
- 컬럼: Module, Part Type, Part Name, Item Name, Actual Value, Spec, Status, Message
- 색상 코딩:
  - 🟢 초록색: PASS
  - 🔴 빨간색: FAIL
  - 🔵 파란색: CHECK (NEW!)
  - ⚪ 회색: NO_SPEC
  - 🟠 주황색: ERROR

#### Sheet 3: Failed Items (실패 항목)
- 실패한 항목만 필터링
- 빠른 문제 파악 및 조치 가능

### 파일명 형식
```
QC_Report_{프로필명}_{날짜시간}.xlsx
예: QC_Report_NX-Wafer_2025-12-28_19-13-29.xlsx
```

---

## 🎨 UI 가이드

### 색상 코드
| 색상 | 의미 | 설명 |
|------|------|------|
| 🟢 초록색 | PASS | 검사 통과 |
| 🔴 빨간색 | FAIL | 검사 실패 |
| 🔵 파란색 | CHECK | 값 확인 (판정 없음) |
| ⚪ 회색 | NO_SPEC | 검사 규격 없음 |
| 🟠 주황색 | ERROR | 검사 중 오류 발생 |

### Summary 표시
```
Validated: PASS/FAIL 검증을 수행한 항목 수
Checked Only: CHECK 타입으로 값만 확인한 항목 수
Pass Rate: Validated 항목 중 PASS 비율 (CHECK 제외)
```

---

## ❓ 문제 해결

### DB 로딩 실패
**증상**: "Failed to load DB" 에러 메시지

**해결 방법**:
1. DB 경로가 올바른지 확인
2. DB 폴더에 `DB.xml` 파일이 있는지 확인
3. 폴더 접근 권한 확인
4. XML 파일 형식 오류 확인

### Export 실패
**증상**: "Permission denied" 에러

**해결 방법**:
1. **동일한 파일명의 Excel이 열려있지 않은지 확인** (가장 흔한 원인)
2. 저장 경로에 쓰기 권한이 있는지 확인
3. 충분한 디스크 공간이 있는지 확인

### 프로필이 표시되지 않음
**증상**: 프로필 드롭다운이 비어있음

**해결 방법**:
1. `config/qc_specs.json` 파일이 존재하는지 확인
2. JSON 파일 형식이 올바른지 검증
3. Profile Manager에서 새 프로필 생성

### Profile Manager/Editor에서 Check 옵션이 안 보임
**증상**: Range, Exact만 보이고 Check가 없음

**해결 방법**:
1. **프로그램 완전 종료** (터미널 포함)
2. Python 캐시 삭제 (선택):
   ```bash
   Remove-Item -Path "src\ui\__pycache__" -Recurse -Force
   Remove-Item -Path "src\core\__pycache__" -Recurse -Force
   ```
3. 프로그램 재시작

---

## 📁 프로젝트 구조

```
DB_Compare/
├── main.py                      # 프로그램 진입점
├── requirements.txt             # Python 패키지 목록
├── README.md                    # 이 문서
├── config/
│   └── qc_specs.json           # QC 프로필 데이터
├── src/
│   ├── core/                    # 핵심 로직
│   │   ├── xml_parser.py       # XML 파싱
│   │   ├── db_extractor.py     # DB 추출
│   │   ├── spec_manager.py     # 프로필 관리
│   │   └── comparator.py       # QC 비교 로직
│   ├── ui/                      # 사용자 인터페이스
│   │   ├── main_window.py      # 메인 창
│   │   ├── profile_manager.py  # 프로필 관리자
│   │   ├── profile_editor.py   # 프로필 편집기
│   │   ├── spec_dialog.py      # Spec 설정 (Editor용)
│   │   └── spec_item_editor.py # Spec 설정 (Manager용)
│   └── utils/                   # 유틸리티
│       └── report_generator.py # Excel 리포트 생성
└── assets/
    └── icon.ico                # 애플리케이션 아이콘 (선택)
```

---

## 🔒 보안

### 프로필 관리 접근
- Profile Manager는 비밀번호로 보호됩니다
- 현재 비밀번호: `pqclevi`
- 승인된 사용자만 프로필 생성/수정/삭제 가능

### 데이터 보호
- DB 파일은 읽기 전용으로만 접근
- 원본 DB 변경 없음
- 모든 설정은 별도 JSON 파일에 저장

---

## 🛠️ 개발자 정보

**프로젝트명**: DB_Compare - QC Inspection Tool  
**버전**: 1.0.0  
**개발자**: Levi.Beak  
**이메일**: levi.beak@parksystems.com  
**회사**: Park Systems  
**개발 완료**: 2025년 12월 28일

### 기술 스택
- **언어**: Python 3.11+
- **GUI**: CustomTkinter
- **리포트**: OpenPyXL
- **구조**: MVC 패턴

### 업데이트 이력
- **v1.0.0** (2025-12-28)
  - ✅ 초기 릴리즈
  - ✅ 3가지 검증 타입 구현 (Range, Exact, Check)
  - ✅ 유연한 Range 지원 (Min만, Max만, 둘 다)
  - ✅ 통합 UI (Profile Manager + Editor)
  - ✅ Excel 보고서 CHECK 지원
  - ✅ 프로필 편집 워크플로우 개선
  - ✅ UI/UX 최적화 완료
  - ✅ 안정성 및 오류 처리 완료

---

## 📞 지원

문제가 발생하거나 기능 요청이 있으면 아래로 연락주세요:

**이메일**: levi.beak@parksystems.com  
**팀**: XE Service Quality Control Team

---

## 📄 라이선스

이 소프트웨어는 Park Systems 내부 사용을 위해 개발되었습니다.  
외부 배포 및 사용은 금지됩니다.

**Copyright © 2025 Park Systems. All rights reserved.**

---

## 🎓 추가 학습 자료

### QC 프로필 JSON 형식

#### Base Profile
```json
{
  "base_profiles": {
    "Common_Base": {
      "description": "Common base specs",
      "specs": {
        "Dsp": {
          "Info": {
            "General": [
              {
                "item_name": "FrequencyHz",
                "validation_type": "range",
                "min_spec": 70,
                "max_spec": 90,
                "unit": "Hz",
                "enabled": true
              }
            ]
          }
        }
      }
    }
  }
}
```

#### Equipment Profile
```json
{
  "equipment_profiles": {
    "NX-Wafer": {
      "description": "NX-Wafer specific profile",
      "inherits_from": "Common_Base",
      "overrides": {
        "Dsp": {
          "Info": {
            "General": [{
              "item_name": "DisabledItem",
              "enabled": false
            }]
          }
        }
      },
      "additional_checks": {
        "Dsp": {
          "Info": {
            "General": [
              {
                "item_name": "NewCheckItem",
                "validation_type": "check",
                "unit": "V",
                "enabled": true
              },
              {
                "item_name": "MinOnlyItem",
                "validation_type": "range",
                "min_spec": 20.0,
                "unit": "°C",
                "enabled": true
              }
            ]
          }
        }
      }
    }
  }
}
```

### 검증 타입 상세

#### 1. Range (범위 검증)
```json
// 양쪽 값
{
  "validation_type": "range",
  "min_spec": 70.0,
  "max_spec": 90.0,
  "unit": "Hz"
}

// Min만 (≥)
{
  "validation_type": "range",
  "min_spec": 20.0,
  "unit": "°C"
}

// Max만 (≤)
{
  "validation_type": "range",
  "max_spec": 100.0,
  "unit": "V"
}
```

#### 2. Exact (정확 일치)
```json
{
  "validation_type": "exact",
  "expected_value": "Auto",
  "unit": ""
}
```

#### 3. Check (값 확인만)
```json
{
  "validation_type": "check",
  "unit": "Hz"
}
```

---

## 💡 사용 팁

### Tip 1: 효율적인 프로파일 관리
```
1. Common_Base에 공통 항목 80% 설정
2. 장비별 프로파일에서 상속 (inherits_from)
3. 차이점만 overrides 또는 additional_checks에 추가
```

### Tip 2: Check 타입 활용
```
- 단순 확인이 필요한 항목 (버전, ID 등)
- PASS/FAIL 판정이 불필요한 경우
- 데이터 수집 목적
```

### Tip 3: 유연한 Range 사용
```
- Min만: 최소 기준만 있는 경우 (온도 ≥ 20°C)
- Max만: 최대 기준만 있는 경우 (전압 ≤ 5V)
- 둘 다: 정확한 범위 (주파수 70-90Hz)
```

---

**즐거운 QC 검사 되세요! 🚀**
