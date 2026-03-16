# QC Profile Manager — 사용자 워크플로우

> **목적**: 장비 모델별 QC 스펙 프로파일을 생성, 편집, 공유하는 관리 도구  
> **진입**: 메인 화면 툴바 **[Profile Manager]** 버튼 (관리자 비밀번호 필요)

---

## 화면 구성

```
┌──────────────────────────────────────────────────┐
│             QC Profile Manager                │
├──────────┬───────────────────────────────────────┤
│ Profiles │  Spec Items (64 items)     🔍 Search  │
│          │  [🌲 Group View toggle]               │
│ NX-Wafer │  ┌──────────────────────────────────┐ │
│ NX-Plus  │  │ Module  PartType  Part  Item ... │ │
│          │  │ Dsp     XScanner  100um ...       │ │
│  [New]   │  │ ...                              │ │
│  [Edit]  │  └──────────────────────────────────┘ │
│  [Delete]│                                       │
│  ────────│                                       │
│ [Export] │                            [Close]    │
│ [Import] │                                       │
└──────────┴───────────────────────────────────────┘
```

| 영역 | 기능 |
|---|---|
| 좌측 패널 | 프로파일 목록, CRUD 버튼, Export/Import |
| 우측 패널 | 선택된 프로파일의 스펙 항목 목록 |
| 상단 Search | 항목명으로 실시간 필터링 |
| Group View | Table ↔ Tree 뷰 전환 토글 |

---

## 핵심 기능 워크플로우

### 1. 프로파일 조회

1. 좌측 목록에서 프로파일 클릭 (예: `NX-Wafer`)
2. 우측에 해당 프로파일의 **전체 스펙 항목** 표시
   - **상속 적용 후** 최종 결과가 표시됨 (`Common_Base` + 장비별 Override + Additional)
3. **Table 뷰** (기본): Module / PartType / Part / Item / Type / Spec / Unit 7컬럼
4. **Tree 뷰** (🌲 토글 ON): Module → PartType → Part → Item 계층 구조

### 2. 스펙 값 즉시 편집 (더블클릭)

1. Table 뷰에서 원하는 항목 **더블클릭**
2. **Spec Item Editor** 대화상자 팝업
3. Validation Type에 따라 편집 필드가 달라짐:
   - **Range**: Min Spec, Max Spec 입력
   - **Exact**: Expected Value 입력
   - **Check**: 값 기록 전용 (편집 불필요)
4. 저장 클릭 → 프로파일 JSON에 즉시 반영
5. 기존 항목 수정 → `overrides`에 기록
6. 새 항목 추가 → `additional_checks`에 기록

### 3. 새 프로파일 생성

1. **[New]** 클릭
2. DB 폴더 선택 → 프로파일 이름 입력
3. **Profile Editor** 창 열림:
   - 선택한 DB에서 자동으로 항목 목록을 추출
   - 각 항목에 대해 Validation Type / Spec 값 설정
   - `Common_Base` 상속 기반으로 기본값 자동 채움
4. 저장 → `config/profiles/{이름}.json` 파일 생성

### 4. 기존 프로파일 편집

1. 프로파일 선택 → **[Edit]** 클릭
2. DB 폴더 선택 (현재 장비 DB 경로)
3. Profile Editor에서 항목별 스펙 수정/추가/삭제
4. 저장 → JSON 파일 업데이트

### 5. 프로파일 삭제

1. 프로파일 선택 → **[Delete]** 클릭
2. 확인 대화상자 → 삭제 시 `config/profiles/{이름}.json` 파일 삭제
3. `Common_Base`는 삭제 불가 (보호됨)

### 6. 프로파일 이름 변경

1. 좌측 프로파일 목록에서 **우클릭** → "Rename Profile"
2. 새 이름 입력 → JSON 파일명 변경 + 내부 참조 업데이트

### 7. 스펙 항목 삭제

1. 우측 스펙 목록에서 항목 **우클릭** → "Delete Item"
2. 해당 항목이 `excluded_items`에 추가되어 비활성화
3. 상속 구조 때문에 `Common_Base`에서 오는 항목은 삭제가 아닌 **제외** 처리

### 8. 검색

1. 우측 상단 검색창에 항목명 입력
2. **실시간 필터링** — 매칭되는 항목만 표시
3. 매칭 항목은 **주황색 하이라이트** 표시
4. 검색어 지우면 전체 목록 복원

---

## 프로파일 공유 (Export / Import)

### Export (내보내기)

1. 프로파일 선택 → **[📤 Export]** 클릭
2. 저장 위치 선택 → `{프로파일명}_{날짜시간}.json` 파일 생성
3. 내보낸 파일에는 프로파일 메타데이터 + 전체 스펙 데이터 포함

### Import (가져오기)

1. **[📥 Import]** 클릭 → JSON 파일 선택
2. 같은 이름의 프로파일이 존재하면:
   - **덮어쓰기** 또는 **새 이름으로 저장** 중 선택
3. Import 완료 → 프로파일 목록에 자동 추가

---

## 프로파일 상속 구조

```
Common_Base (config/common_base.json)
    ├── NX-Wafer (config/profiles/NX-Wafer.json)
    │     ├── inherits_from: "Common_Base"
    │     ├── overrides: { ... }          ← 기존 항목 값 재정의
    │     ├── additional_checks: { ... }  ← 모델 전용 추가 항목
    │     └── excluded_items: [...]       ← 제외 항목 (와일드카드 지원)
    │
    └── NX-Wafer_Plus (config/profiles/NX-Wafer_Plus.json)
          └── 동일 구조
```

**최종 스펙 계산**: `Common_Base specs` → `overrides 적용` → `additional_checks 추가` → `excluded_items 제거`

---

## 대표 시나리오

### 신규 모델 프로파일 등록
1. Profile Manager → [New] → DB 선택 → 이름 입력
2. Profile Editor에서 DB 항목 기반 스펙 설정
3. 저장 → 즉시 메인 화면 프로파일 드롭다운에 반영

### 기존 모델 스펙 미세 조정
1. 프로파일 선택 → 해당 항목 더블클릭
2. Min/Max 또는 Expected Value 수정 → 저장
3. 변경된 값은 `overrides`에 기록 (Common_Base 원본 유지)

### 타 PC / 팀원에게 프로파일 전달
1. [📤 Export] → USB/이메일로 JSON 전달
2. 상대방 PC에서 [📥 Import] → 같은 프로파일 적용
