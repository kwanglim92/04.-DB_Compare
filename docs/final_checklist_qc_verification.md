# Final Checklist QC Verification Checklist

이 문서는 `Final Checklist QC` 기능을 출고 전 검수할 때 사용하는 수동 체크리스트와 에이전트 자동 검증 기준을 정리한다.

## 검증 전 준비

- 최신 브랜치가 `main` 기반인지 확인한다.
- QC를 먼저 실행해 `qc_report`가 준비된 상태에서 `Final Checklist QC`를 연다.
- 실제 checklist 샘플은 최소 2개 이상 준비한다.
- Mismatch가 많은 샘플 1개를 별도로 준비한다.
- 서버 연결 검증은 연결 가능 환경과 오프라인 환경을 각각 확인한다.
- Final QC 창은 메인창을 막지 않는 독립 창으로 열리는지 확인한다.
- checklist 파일 선택 창은 DB 폴더가 아니라 마지막 checklist 폴더에서 시작하는지 확인한다.

## 1. 수동 체크리스트

### A. 진입점 / 최신 GUI 유지 확인

- [ ] 메인 화면에 기존 `Auto-Fill Checklist` 대신 `Final Checklist QC` 버튼이 보인다.
- [ ] 기존 `Review Checklist`, 서버 설정, Admin, Sync 관련 메뉴/버튼이 사라지지 않았다.
- [ ] `Final Checklist QC` 버튼 클릭 시 새 QC 다이얼로그가 열린다.
- [ ] `Final Checklist QC` 창이 열린 뒤에도 메인 창을 계속 조작할 수 있다.
- [ ] 우측 상단 `English / 한국어` 전환 버튼과 `Maximize / Restore` 버튼이 보인다.
- [ ] 서버 연결 설정이 되어 있는 환경에서 Final QC가 기존 `SyncManager` 흐름을 사용한다.
- [ ] 서버가 없어도 로컬 캐시 기반으로 분석이 가능하다.

### B. Preflight 검사

- [ ] checklist 파일이 없거나 열 수 없으면 `Error`로 적용이 차단된다.
- [ ] `통합_*` 시트가 없으면 경고 또는 차단 메시지가 표시된다.
- [ ] `표지` 시트는 분석/기입 대상에서 제외된다.
- [ ] B/C/G/H/M 열 구조가 검사된다.
- [ ] G열 수식 셀은 `Blocked/Protected`로 분류된다.
- [ ] 병합 셀, 숨김 행, 보호 시트는 Preflight에 표시된다.
- [ ] QC lookup이 비어 있으면 적용 전 위험 메시지가 표시된다.
- [ ] `Error`가 없으면 분석 결과 테이블로 진행된다.

### C. 분석 결과 분류

- [ ] G열 값이 QC 값과 같으면 `OK`로 표시된다.
- [ ] G열이 비어 있고 DB_Key/QC 매칭이 있으면 `Missing`으로 표시된다.
- [ ] G열 값이 QC 값과 다르면 `Mismatch`로 표시된다.
- [ ] DB_Key 또는 매핑을 찾지 못하면 `Unmapped`로 표시된다.
- [ ] 수식 셀, 그룹 헤더, 보호 대상은 `Protected`, `SkippedGroup`, `Blocked`로 표시된다.
- [ ] 값 비교가 불가능한 행은 `NonComparable` 또는 `HighRisk`로 분류된다.

### D. 위험도 / 추천 액션

- [ ] `explicit/learned/exact` 매칭의 Missing은 `Safe + Fill QC Value`로 표시된다.
- [ ] `explicit/learned/exact` 매칭의 Mismatch는 `Safe + Replace with QC Value`로 표시된다.
- [ ] fuzzy/manual candidate/복수 후보는 `Review + Reviewer Confirm`로 표시된다.
- [ ] 타입이 다르거나 차이가 큰 Mismatch는 `HighRisk`로 표시된다.
- [ ] formula/group/header/QC N/A/unmapped는 `Blocked + Do Not Write`로 표시된다.

### E. 승인 동작

- [ ] 기본 상태에서는 아무 행도 자동 기입 대상으로 확정되지 않는다.
- [ ] 승인 열은 미승인 `☐`, 승인 `☑`, 예외 `!` 형태로 표시된다.
- [ ] 승인 열 클릭 시 writable 행만 개별 승인/해제된다.
- [ ] `Blocked`, `Protected`, `SkippedGroup`, `Missing in Checklist` 진단 행은 승인 열을 클릭해도 승인되지 않는다.
- [ ] `Approve Safe Corrections` 클릭 시 Safe Missing/Mismatch만 승인 후보로 체크된다.
- [ ] Review/HighRisk/Blocked 행은 자동 승인 후보에 포함되지 않는다.
- [ ] `Unapprove Selected` 클릭 시 선택된 승인 행만 해제된다.
- [ ] `Reset All` 클릭 시 확인 팝업이 표시되고, Yes일 때만 모든 승인/예외가 초기화된다.
- [ ] 개별 행 선택 후 `Approve Selected`가 정상 동작한다.

### F. 필터 / 예외 / 복사

- [ ] 필터의 `Mismatch` 선택 시 Mismatch 행만 표시된다.
- [ ] `Needs Attention`, `Profile Matched`, `Missing in Checklist` 필터가 각각 목적에 맞게 동작한다.
- [ ] 각 행에서 `Current G`, `QC Value`, `Delta`, `DB_Key`, `Risk`를 비교할 수 있다.
- [ ] 기본 판단은 `Replace with QC Value` 방향으로 보인다.
- [ ] 예외로 유지할 행은 `Set Exception / 예외 설정`으로 사유를 입력할 수 있다.
- [ ] Exception 행은 G열이 변경되지 않고 로그에 사유가 남는다.
- [ ] 우클릭 메뉴 또는 `Ctrl+C`로 셀 값을 복사할 수 있다.
- [ ] `Copy DB Key`는 화면 표시값이 아니라 내부 DB key 원문을 복사한다.
- [ ] `Copy Row`는 Excel에 붙여넣기 가능한 tab-separated 값으로 복사된다.

### G. Apply 결과 파일

- [ ] 원본 checklist 파일은 수정되지 않는다.
- [ ] 결과 파일은 같은 폴더에 `_QC_Checked_AutoFilled_YYYYMMDD_HHMMSS.xlsx` 형식으로 생성된다.
- [ ] 승인된 Missing/Mismatch 행만 G열에 QC 값이 기입된다.
- [ ] 승인하지 않은 행은 결과 사본에서도 변경되지 않는다.
- [ ] 수식 셀, 그룹 헤더, `표지` 시트는 절대 변경되지 않는다.
- [ ] `Write DB_Key to M column (internal copy)` 기본값이 ON이다.
- [ ] DB_Key 옵션 ON 상태에서 승인 행의 M열이 채워진다.
- [ ] 결과 사본에 `_AutoFill_Log` 시트가 생성된다.
- [ ] 로그에 row, before/after status, risk, action, previous G, QC value, DB_Key, source, confidence, reviewer decision, exception reason이 남는다.
- [ ] Apply 직후 재분석 결과에서 승인된 행은 `OK`가 된다.

### H. Profile Coverage / 누락 진단

- [ ] 상단 Profile Coverage 요약에 checklist mapped / profile items / missing / extra count가 표시된다.
- [ ] `NO_SPEC` 항목은 Profile Coverage count에서 제외된다.
- [ ] `Missing in Checklist` 필터는 Profile에는 있지만 checklist DB_Key에 없는 항목을 진단 행으로 표시한다.
- [ ] `Missing in Checklist` 진단 행은 승인/apply 대상이 아니다.

### I. 매핑 학습

- [ ] Unmapped 행에서 후보 DB key를 선택할 수 있다.
- [ ] 사용자가 후보를 선택하고 승인한 행만 learned mapping으로 저장된다.
- [ ] 다음 분석에서 해당 행은 `learned`, confidence `0.95`로 매칭된다.
- [ ] 서버 연결 가능 시 `checklist_mappings`에 upsert된다.
- [ ] 서버 연결 불가 시 로컬 JSON 캐시에 저장된다.

## 2. 에이전트 자동 검증

에이전트는 synthetic checklist를 만들고 pytest를 실행해 반복 가능한 로직을 검증한다. UI 문구와 실제 현장 양식 호환성은 사람이 최종 확인한다.

### 실행 명령

```powershell
python -m pytest tests\test_checklist_final_qc.py -q
```

전체 회귀 검증이 필요하면 다음을 실행한다.

```powershell
python -m pytest -q
```

### 자동 검증 대상

- [ ] 분류 로직: `OK`, `Missing`, `Mismatch`, `Unmapped`, `Protected`, `SkippedGroup`
- [ ] 위험도: `Safe`, `Review`, `HighRisk`, `Blocked`
- [ ] 승인 행만 결과 사본에 반영되는지
- [ ] 원본 파일이 변경되지 않는지
- [ ] DB_Key 기본 ON 동작
- [ ] `_AutoFill_Log` 생성 및 필수 컬럼 기록
- [ ] Apply 후 재분석 결과가 `OK`로 바뀌는지
- [ ] learned mapping이 다음 분석에 반영되는지
- [ ] Preflight가 missing file, empty QC lookup, formula, hidden row, merged cell, sheet protection을 감지하는지
- [ ] 승인 목록에 Blocked 행이 들어와도 실제로 쓰지 않는지
- [ ] 승인 열 개별 토글, 선택 해제, 전체 초기화 확인 팝업이 동작하는지
- [ ] DB key / row 복사 기능이 내부 key 원문을 유지하는지
- [ ] Profile Coverage와 Missing in Checklist 진단 행이 정확히 계산되는지

## 3. 사람이 직접 확인해야 하는 항목

- [ ] UI 문구가 현장 작업자에게 명확한지
- [ ] Mismatch 필터 화면에서 비교가 충분히 쉬운지
- [ ] 실제 고객 checklist 양식에서 열 구조가 어긋나지 않는지
- [ ] Exception 사유 입력 흐름이 작업 방식에 맞는지
- [ ] DB_Key가 고객 전달본에 노출되면 안 되는 케이스가 구분되는지
- [ ] 독립 창/최대화 상태에서 다중 모니터 사용성이 괜찮은지

## 4. 권장 검증 순서

1. 에이전트가 synthetic checklist 자동 테스트를 실행한다.
2. 실제 현장 checklist 샘플 2~3개로 수동 체크리스트를 수행한다.
3. Mismatch가 많은 샘플로 `Approve Safe Corrections -> Mismatch 필터 -> Apply -> 재분석` 흐름을 확인한다.
4. 서버 연결 ON/OFF 각각에서 learned mapping 저장 위치를 확인한다.
5. 독립 창 상태에서 메인창의 Profile Viewer 검색과 Final QC를 병행 확인한다.

## 5. 검증 기록 템플릿

| Date | Tester | Checklist Sample | Server Mode | Auto Test | Manual Result | Notes |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  | Online / Offline | Pass / Fail | Pass / Fail |  |

