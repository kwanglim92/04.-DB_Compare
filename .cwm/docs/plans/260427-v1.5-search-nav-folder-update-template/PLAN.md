# v1.5.0 통합 계획서 — 검색 네비 / 서버폴더 보강 / 자동업데이트 / 리포트 템플릿

## 개요
- **목적**: DB 검사 도구 v1.5.0 — 4개 기능 영역(F4/F5/F13/F14) 통합 구현
- **범위**: tree_view.py, main_window.py, db_extractor.py, report_generator.py, admin_window.py + 신규 3개 모듈
- **예상 Phase**: A(F4) → B(F5) → C(F13) → D(F14) → E(문서) → F(검증/커밋)

## 현재 상태 분석

### tree_view.py (421줄)
- `search()`: `_search_index` 기반 전체 강조, 첫 번째 매치로 scroll
- `_highlighted_iids`, `'search_hit'` 태그 이미 존재
- **없는 것**: `_search_matches` 리스트, `_current_match_idx`, `next_match()`/`prev_match()`/`_goto_match()`, `'search_active'` 태그

### main_window.py (1202줄)
- `db_search_entry` + `db_search_count_label` 이미 존재 (F1 검색 UI)
- `open_db()`: `filedialog.askdirectory()` — `initialdir` 전달 안 함
- `db_root_path`는 `settings.json`에 저장되지만 다이얼로그에 미반영
- **없는 것**: ▲/▼ 버튼, 현재/총 매치 라벨, 검증 분기, `initialdir` 전달

### db_extractor.py (220줄)
- `extract_all_modules()`: `iterdir()` — PermissionError 미처리
- `extract_module_parts()`: 권한 에러 미처리
- `build_hierarchy()`: FileNotFoundError는 처리, 권한 에러는 누락
- **없는 것**: `validate_db_root()`, `find_db_root_in_subtree()`

### report_generator.py (241줄)
- `ExcelReportGenerator.__init__()` — 인수 없음, 모든 스타일 하드코딩
- Summary/All Items/Failed Items 3개 시트 고정
- **없는 것**: template 파라미터, 로고 삽입, Cover Page, 시트 토글

### admin_window.py (178줄)
- 기존 탭: Server Settings, QC Profiles 등
- **없는 것**: "리포트 템플릿" 탭, "수동 업데이트 체크" 버튼

## 구현 계획

### Phase A — F4: 검색 매치 Prev/Next 네비게이션

**A.1 tree_view.py — 상태/태그 추가**
- `__init__`에 `self._search_matches: list = []`, `self._current_match_idx: int = -1` 추가
- `'search_active'` 태그 등록: `background='#ff9800', foreground='#000'`

**A.2 tree_view.py — `search()` 수정**
- 매치 리스트를 `self._search_matches`에 저장
- `self._current_match_idx = 0` 리셋 후 `_goto_match(0)` 호출

**A.3 tree_view.py — `_goto_match()` 신규**
- `'search_active'` 태그를 현재 매치에만 적용 (이전 active 제거)
- `self.tree.see()` + `self.tree.selection_set()`

**A.4 tree_view.py — `next_match()` / `prev_match()` 신규**
- wraparound (`% len`), `(current_1based, total)` 반환

**A.5 main_window.py — ▲/▼ 버튼 + 카운트 라벨**
- 검색 헤더에 `[검색 입력] [▲] [▼] [3 / 12]` 레이아웃
- 매치 ≥ 2일 때만 버튼 활성

**A.6 main_window.py — 키 바인딩**
- 검색창: `<Return>` = 다음, `<Shift-Return>` = 이전
- 전역: `<F3>` = 다음, `<Shift-F3>` = 이전

**A.7 main_window.py — `_do_db_search` 수정**
- 카운트 라벨 형식: `"N matches"` → `"1 / N"` (active 매치 표시)
- 버튼 활성/비활성 연동

### Phase B — F5: Open DB 서버 폴더 접근 보강

**B.1 db_extractor.py — 권한 에러 graceful skip**
- `extract_all_modules()`: `iterdir()` → `try/except (PermissionError, OSError)`
- `extract_module_parts()`: 경로 접근 시 동일 처리

**B.2 db_extractor.py — `validate_db_root()` 신규**
- 반환: `("valid"|"no_module_dir"|"permission_denied"|"empty", path_str)`
- Module/ 존재 여부, 접근 가능 여부, 내용 유무 검사

**B.3 db_extractor.py — `find_db_root_in_subtree(start, max_depth=3)` 신규**
- BFS로 max_depth까지 Module/ 탐색
- 권한 에러 분기 skip, 발견 시 Module/ 부모 경로 반환

**B.4 main_window.py — `open_db()` initialdir 추가**
- 우선순위: `self.db_root` → `settings.db_root_path` → `''`

**B.5 main_window.py — `_load_db_thread` 검증 분기**
- `validate_db_root()` → valid면 진행
- `no_module_dir` → `find_db_root_in_subtree()` → 발견 시 확인 다이얼로그
- `permission_denied` / `empty` → 안내 메시지

**B.6 main_window.py — 로드 성공 시 `db_root_path` 저장**
- `_on_db_loaded()`에서 `settings.json.db_root_path` 업데이트

### Phase C — F13: 자동 업데이트 체크

**C.1 DB 스키마**
- `dbmanager-server/init/02_app_releases.sql` 생성
- `app_releases` 테이블: id, version, release_date, download_url, release_notes, is_critical, min_compatible_version

**C.2 src/utils/version.py — 신규**
- `APP_VERSION = "1.5.0"`
- `parse_version(s) -> tuple[int,int,int]`
- `is_newer(a, b) -> bool`

**C.3 src/core/update_checker.py — 신규**
- `class UpdateChecker`
- `check_async(callback)`: 백그라운드 스레드, psycopg2로 SELECT, 실패 시 None 반환

**C.4 src/ui/update_dialog.py — 신규**
- `UpdateAvailableDialog`: 현재/최신 버전, Release Notes, [다운로드] [나중에] [무시]
- `is_critical=True` → "나중에"/"무시" 비활성

**C.5 main_window.py — 앱 시작 시 비동기 체크**
- `__init__` 마지막에 `UpdateChecker().check_async(self._on_update_result)` (온라인 모드만)
- `skipped_versions` 목록과 비교

**C.6 settings.json — skipped_versions**
- `load_settings()`에서 `skipped_versions: list[str]` 읽기
- 무시 버튼 클릭 시 저장

**C.7 Admin 창 — "지금 확인" 버튼**
- `server_settings` 탭 하단에 추가

### Phase D — F14: Excel 리포트 템플릿 커스터마이징

**D.1 config/report_template.json — 기본값 파일**
- company, title_template, engineer_name, header_color, footer_text
- sheets: summary/all_items/failed_items/cover_page(false)
- columns: show_unit, show_description

**D.2 src/utils/template_helper.py — 신규**
- `load_template()`, `save_template()`, `validate_template()`
- `apply_placeholders(template_str, ctx) -> str`

**D.3 src/utils/report_generator.py — template 연동**
- `__init__(template: dict = None)` 추가
- 색상/제목/회사명/로고/Footer를 template에서 읽기
- sheets 토글 (cover_page 신규 시트 포함)
- 로고: `openpyxl.drawing.image.Image` (경로 없으면 skip)

**D.4 src/ui/report_template_panel.py — 신규**
- 회사 정보, 타이틀 템플릿, 헤더 색상, Footer 입력 UI
- 시트 체크박스 4개
- [기본값 초기화] [미리보기] [저장] 버튼

**D.5 admin_window.py — "리포트 템플릿" 탭 추가**
- `ReportTemplatePanel` 삽입

**D.6 미리보기 기능**
- 더미 QC 데이터로 임시 Excel 생성 → `os.startfile()`

### Phase E — 문서 / 릴리즈
- `docs/CHANGELOG.md` v1.5.0 섹션
- 타이틀 버전 v1.4.0 → v1.5.0 (version.py import)
- `사용설명서.md` 업데이트

### Phase F — 검증 & 커밋
- `python -m pytest tests/` 회귀 통과
- 신규 단위 테스트: version, db_extractor, update_checker, template_helper
- 수동 시나리오 검증
- EXE 빌드 테스트
- main 브랜치 커밋 + push

## 기술 선택
- **psycopg2**: 기존 sync_manager와 동일 패턴, 연결 타임아웃 5초
- **os.startfile()**: Windows 전용, UNC/HTTP 경로 모두 처리 (D1=UNC 권장)
- **openpyxl**: 기존 report_generator와 동일 라이브러리
- **threading.Thread(daemon=True)**: 업데이트 체크 블로킹 방지
- **로컬 JSON**: v1.5에서는 서버 동기화 없이 로컬 파일만 (D3)

## 결정 사항 (확정)
| ID | 결정 | 선택 |
|----|------|------|
| D1 | 다운로드 방식 | UNC `os.startfile()` |
| D2 | is_critical 강제 업데이트 | 사용 |
| D3 | 리포트 템플릿 저장 위치 | 로컬 JSON만 (v1.5) |
| D4 | Cover Page 기본값 | OFF |
| D5 | Enter 키 동작 | Enter=다음, Shift+Enter=이전 |

## 리스크
- **F13 `app_releases` 미생성 환경**: silent fail로 처리, 앱 동작에 영향 없음
- **F14 로고 경로 네트워크 지연**: 로고 skip + warning (앱 죽지 않음)
- **F5 UNC 경로 한글**: Path 객체로 처리, casefold 비교 없이 exists()만 사용
- **F4 `search_active` + `search_hit` 동시**: `_goto_match`에서 search_hit 유지, search_active만 현재 매치에 추가
