# WORKLOG

**Last Updated**: 2026-04-29  
**Current Branch**: `main`  
**Latest Pushed Commit**: `fa0f13f docs: update Final Checklist QC workflow`

---

## 완료

- Final Checklist QC 핵심 흐름 구현 완료
  - checklist 원본 보존, 내부 결과 사본 생성
  - 승인된 `Missing/Mismatch` 행만 G열에 QC 값 기입
  - DB_Key는 내부 사본 M열에 기본 ON으로 기록
  - `_AutoFill_Log` 시트에 변경 이력, 위험도, 결정, 예외 사유 기록
  - 적용 직후 결과 사본 재분석

- Final Checklist QC 검수 기능 고도화 완료
  - Preflight 검사
  - `OK`, `Missing`, `Mismatch`, `Unmapped`, `Protected`, `SkippedGroup`, `NonComparable` 분류
  - `Safe`, `Review`, `HighRisk`, `Blocked` 위험도
  - Profile Coverage 요약
  - `All Rows`, `Needs Attention`, `Mismatch`, `Profile Matched`, `Missing in Checklist` 필터
  - `Missing in Checklist` 진단 행 추가

- Final Checklist QC UI/UX 개선 완료
  - English/Korean 전환
  - 승인 열 개별 토글: `☐`, `☑`, `!`
  - `Approve Selected`, `Unapprove Selected`, `Approve Safe Corrections`, `Set Exception`, `Reset All`
  - `Reset All` 확인 팝업
  - 도움말 tooltip 안정화
  - `Ctrl+C`, 우클릭 메뉴로 셀/DB_Key/행 복사
  - `Check Item` 열 폭 확대, `Checklist Measurement (G)` 헤더 적용
  - 독립 창(modeless) 동작
  - Maximize/Restore 버튼
  - DB 폴더 경로와 checklist 파일 선택 경로 분리

- Run QC / N/A Items Review 개선 완료
  - `Save this selection to profile` 기능 제거
  - N/A 제외 선택은 해당 QC 재실행에만 임시 적용
  - profile DB/JSON 수정 경로 제거

- Admin UI 개선 완료
  - Admin Window, Server Settings, Spec Management, Report Template 사용자 표시 문구 영어화
  - Profile 삭제 시 기존 경고 후 관리자 비밀번호 재입력 필요
  - Spec Add/Edit popup 크기/레이아웃 개선
  - Edit 모드에서 DB key 필드 잠금
  - Range/Exact/Check 저장 검증 강화
  - Spec Management에 `All / Needs Spec Setup` 필터와 `Needs setup: N` badge 추가

- Main/Profile Viewer 개선 완료
  - Profile Viewer 검색창 추가
  - `All / Pass / Check / Fail` 상태 필터와 검색어 AND 조건 적용
  - `Ctrl+F` 검색 포커스, `Esc` 검색 초기화
  - QC 결과 갱신 후 현재 필터/검색 유지

- 문서 업데이트 및 푸시 완료
  - `README.md`, `CHANGELOG.md`, `PRD_DB_Manager.md`, `사용설명서.md`, `final_checklist_qc_verification.md` 갱신
  - `main` 브랜치에 `fa0f13f` 커밋 푸시 완료

- 검증 완료
  - `python -m pytest -q` 결과: `182 passed, 6 skipped`
  - `git diff --check` 문서 공백 오류 없음

---

## 진행중

- v1.6 Final Checklist QC 현장 샘플 검증 단계
  - synthetic test 기준은 통과했으나 실제 고객 checklist 샘플 2~3개 검증 필요
  - Mismatch가 많은 checklist로 승인/예외/적용/재분석 흐름 확인 필요

- learned mapping / 서버 동기화 실제 환경 검증
  - 서버 연결 가능 환경에서 `checklist_mappings` upsert 확인 필요
  - 오프라인 환경에서 로컬 JSON 캐시 저장 및 재사용 확인 필요

- 결과 사본 운영 정책 정리
  - 현재 기본값은 내부 마스터 사본
  - M열 DB_Key 기본 ON
  - 고객 전달용 clean copy export는 후속 기능으로 분리 예정

---

## 다음할일

1. 실제 checklist 샘플 2~3개로 `docs/final_checklist_qc_verification.md` 수동 체크리스트 수행
2. Mismatch가 많은 샘플로 `Approve Safe Corrections -> Mismatch 필터 -> Set Exception -> Apply -> 재분석` 흐름 검증
3. Spec Management에서 신규 Add/Import 후 `Needs Spec Setup` 필터가 누락 설정을 잘 잡는지 현장 데이터로 확인
4. Profile Viewer 검색이 실제 profile 확인 업무에 충분한지 사용성 점검
5. PyInstaller 빌드 후 EXE 환경에서 Final Checklist QC, rapidfuzz, openpyxl, 서버 sync 동작 확인
6. 고객 전달용 사본이 필요한 경우 `Export Customer Clean Copy` 설계 및 구현 여부 결정
7. v1.6 배포 전 CHANGELOG 릴리즈 섹션을 `work-in-progress`에서 정식 버전으로 전환

---

## 미결이슈

- 결과 사본의 성격
  - 내부 마스터 사본으로 고정할지, 고객 전달 가능 파일로도 허용할지 정책 확정 필요
  - 현재 추천값은 내부 마스터 사본이며 DB_Key M열 기본 ON

- 고객 전달본 DB_Key 노출
  - M열 DB_Key가 고객 전달본에 노출되면 안 되는 케이스가 있을 수 있음
  - clean export 기능으로 M열 비우기/숨김 처리 필요 여부 결정 필요

- 실제 checklist 양식 변형
  - `통합_*` 시트, B/C/G/H/M 열 구조, 병합/숨김/보호 상태가 샘플마다 다를 수 있음
  - 현장 샘플 기반 호환성 확인 필요

- 예외 설정 운영 기준
  - checklist 값을 유지하는 사유 입력 기준과 리뷰 책임자 기준이 필요
  - 예외 행은 G열을 수정하지 않고 `_AutoFill_Log`에만 기록됨

- 서버 연결 환경 차이
  - 온라인/오프라인 전환, 권한, PG 접속 불가 상황에서 learned mapping 저장 위치 확인 필요

- GUI 육안 검증
  - 독립 창, 최대화, 다국어 전환, tooltip, 셀 복사, 다중 모니터 사용성은 실제 앱 실행 상태에서 최종 확인 필요
