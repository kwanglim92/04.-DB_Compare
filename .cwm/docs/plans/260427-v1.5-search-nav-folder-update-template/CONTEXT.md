# v1.5.0 맥락 노트

## 결정 기록
| 결정 사항 | 선택지 | 최종 선택 | 이유 |
|-----------|--------|-----------|------|
| F13 다운로드 방식 | UNC os.startfile / HTTP 다운로드 | UNC os.startfile | 사내 인프라 추가 불필요, Windows 전용 환경 |
| F13 강제 업데이트 | is_critical 사용 / 미사용 | 사용 | 보안 패치 시 강제 필요 |
| F14 템플릿 저장 | 로컬 JSON / 서버 동기화 | 로컬 JSON (v1.5) | 단순성, 서버 동기화는 v1.6+ |
| F14 Cover Page 기본값 | ON / OFF | OFF | 대부분 불필요, 선택적 사용 |
| F5 Enter 키 동작 | Enter=다음 / 즉시검색 유지 | Enter=다음, Shift+Enter=이전 | 네비게이션 일관성 |

## 기존 코드 구조 — 핵심 파악

### tree_view.py 검색 현황 (L302~L379)
- `search(query)`: 모든 매치에 'search_hit' 적용, 첫 매치로 scroll (매치 리스트 리턴만 함)
- `_search_index`: `[(iid, casefold_text)]` 전체 노드
- `_highlighted_iids`: 현재 강조된 iid set
- F4 구현 시 `_search_matches` 별도로 추가 (기존 `_highlighted_iids`와 분리)

### main_window.py open_db (L564~L576)
```python
path = filedialog.askdirectory(title="Select DB Directory")
```
- `initialdir` 없음 → B.4에서 추가
- `db_root_path` settings에서 읽음 (L93) 하지만 다이얼로그에 미전달

### db_extractor.py 권한 취약점 (L47, L70)
- L47: `for item in module_dir.iterdir()` — PermissionError 가능
- `build_hierarchy()` → `extract_all_modules()` → `extract_module_parts()` 체인

### report_generator.py 현재 시트 구성 (L52~L54)
```python
self.create_summary_sheet(wb, qc_report)
self.create_all_items_sheet(wb, qc_report)
self.create_failed_items_sheet(wb, qc_report)
```
- 세 시트 고정, 조건부 생성 없음

### admin_window.py 탭 구조 (178줄)
- 기존 탭 확인 필요 후 "리포트 템플릿" 탭 추가 위치 결정

## 참조 자료
- 기존 Server DB Sync 연결 패턴: `src/core/sync_manager.py` (psycopg2 연결, 5초 timeout)
- 기존 settings 처리: `src/utils/config_helper.py`
- Excel 색상 상수: `src/constants.py` EXCEL_COLORS
- 기존 Admin 탭 패턴: `src/ui/admin_window.py`

## 제약 조건
- **Windows 전용**: `os.startfile()`, UNC 경로
- **Python 3.11+**, CustomTkinter, psycopg2, openpyxl
- **오프라인 모드 지원**: F13은 online 모드일 때만 동작
- **app_releases 테이블 없는 환경**: silent fail 필수 (기존 서버 호환)
- **기존 테스트 66개 회귀 유지**: 변경 시 기존 API 시그니처 유지 또는 default 인수로 하위 호환

## 사용자 요구사항 원문 (결정 사항)
> D1=UNC os.startfile, D2=is_critical 사용, D3=로컬 JSON만, D4=Cover Page 기본 OFF, D5=Enter=다음/Shift+Enter=이전

## 신규 파일 목록
| 파일 | 역할 |
|------|------|
| `src/utils/version.py` | APP_VERSION 상수 + semver 파서 |
| `src/core/update_checker.py` | 비동기 업데이트 체크 |
| `src/ui/update_dialog.py` | 업데이트 알림 다이얼로그 |
| `src/utils/template_helper.py` | 리포트 템플릿 로드/저장/검증 |
| `src/ui/report_template_panel.py` | Admin 리포트 템플릿 편집 UI |
| `config/report_template.json` | 기본 템플릿 설정 파일 |
| `dbmanager-server/init/02_app_releases.sql` | DB 스키마 마이그레이션 |
