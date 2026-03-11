# DB_Compare QC Inspection Tool — 사용자 워크플로우

> **대상**: 반도체 계측 장비 납품/유지보수 담당자  
> **목적**: 장비 DB 설정값을 스펙 기준과 자동 비교하여 QC 검사 결과 보고서 생성

---

## 전체 흐름

```
앱 실행 → DB 열기 → 프로파일 선택 → QC 실행 → 결과 확인 → 보고서 Export
```

---

## Step 1. 앱 실행

`DB_Compare_QC_Tool.exe` 실행  
이전 사용 환경(DB 경로, 프로파일)이 자동 복원됩니다.

**초기 화면 구성:**

| 영역 | 위치 | 내용 |
|---|---|---|
| 툴바 | 상단 | Open DB / Run QC / Export / Profile Manager 버튼 |
| DB STRUCTURE | 좌측 | DB 파일을 열면 장비 계층 구조 표시 |
| QC INSPECTION RESULTS | 우측 상단 | QC 실행 후 Pass/Fail 요약 표시 |
| PROFILE VIEWER | 우측 하단 | 선택된 프로파일의 스펙 항목 목록 |

---

## Step 2. DB 열기

**[Open DB]** 버튼 클릭 → 장비 DB 폴더 선택

> 예: `C:\Park Systems\XEService\DB\`

앱이 폴더 안의 `DB.xml` 및 `Module/*.xml` 파일을 자동 파싱합니다.  
좌측 DB STRUCTURE 트리뷰에 장비 계층 구조가 나타납니다.

```
▼ Dsp
  ▼ XScanner / 100um
    • ServoCutoffFrequencyHz   → 80.0
    • ForceGain                → 1250.0
▼ System
  ▼ MainController / ...
```

DB 로딩 완료 후 **[Run QC]**, **[Export]** 버튼이 활성화됩니다.

---

## Step 3. 프로파일 선택

툴바 드롭다운에서 장비 모델에 맞는 프로파일을 선택합니다.

| 프로파일 | 설명 |
|---|---|
| `NX-Wafer` | NX Wafer 장비 표준 스펙 |
| `NX-Wafer_Plus` | NX Wafer Plus 엄격 스펙 (추가 검사 포함) |

> **프로파일 상속 구조:**  
> `Common_Base` (공통 기준) → `NX-Wafer` (모델별 재정의/추가)

선택 즉시 우측 하단 **PROFILE VIEWER**에 해당 프로파일의 전체 스펙 목록이 업데이트됩니다.

---

## Step 4. QC 실행

**[Run QC]** 버튼 클릭  
백그라운드에서 DB 항목과 스펙을 자동 비교합니다 (UI 응답 유지).

### 검증 방식 3가지

| 검증 타입 | 판정 기준 | 예시 |
|---|---|---|
| **Range** | `min ≤ 실제값 ≤ max` | ServoCutoffFrequency: `[60, 100]` Hz |
| **Exact** | `실제값 == 기대값` | FirmwareVersion: `"3.2.1"` |
| **Check** | 값만 기록 (판정 없음) | SerialNumber |

### 결과 상태

| 상태 | 의미 |
|---|---|
| ✅ `PASS` | 스펙 범위 내 |
| ❌ `FAIL` | 스펙 범위 벗어남 / DB에 항목 없음 |
| 🔍 `CHECK` | 기록 전용 (합격/불합격 없음) |
| ⚠️ `ERROR` | DB에서 값 읽기 실패 |

---

## Step 5. 결과 확인

### 우측 상단 — QC INSPECTION RESULTS

```
✅ PASS: 142    ❌ FAIL: 3    🔍 CHECK: 5    Pass Rate: 97.9%
```

### 좌측 — DB STRUCTURE 트리

각 항목에 PASS/FAIL 색상 뱃지가 표시됩니다.  
FAIL 항목 클릭 → 실제값, 기대 스펙, 벗어난 정도 상세 확인

### 우측 하단 — PROFILE VIEWER

실제값 컬럼이 업데이트되어 스펙 대비 현황을 한눈에 파악할 수 있습니다.

---

## Step 6. 보고서 Export

**[Export]** 버튼 클릭 → Excel(.xlsx) 파일 저장

보고서 포함 내용:
- 검사 일시, 장비 DB 경로, 사용 프로파일
- 항목별 결과 (모듈 > 파트 > 항목명 > 실제값 > 스펙 > 판정)
- 요약 통계 (총 항목 수, PASS/FAIL 수, 합격률)

---

## 부록: 프로파일 관리 (Profile Manager)

**[Profile Manager]** 버튼 클릭 → 별도 창 열기

| 기능 | 방법 |
|---|---|
| 스펙 항목 수정 | 항목 더블클릭 → Range/Exact 값 편집 |
| 새 프로파일 생성 | 기존 프로파일 복제 후 수정 |
| 팀 공유 | Export(JSON) → 상대방 Import |
| 항목 검색 | 검색창에 항목명 입력 |
| 뷰 전환 | Table ↔ Tree 토글 버튼 |

---

## 대표 시나리오

### 장비 납품 전 최종 QC 점검
1. 장비 DB 폴더 열기
2. 해당 모델 프로파일 선택
3. Run QC → FAIL 0건 확인
4. Export → 고객사 제출용 QC 보고서 생성

### 신규 장비 모델 스펙 등록
1. Profile Manager 열기
2. 유사 프로파일 복제
3. 스펙 값 더블클릭으로 수정
4. Export JSON → 팀 공유 / 타 PC에 Import 적용
