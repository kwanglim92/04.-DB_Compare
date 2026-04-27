# v1.5.0 체크리스트

## 컨텍스트 전환 체크
- [x] 사용자 승인 완료
- [x] /compact 안내 출력 완료

---

## Phase A — F4: 검색 매치 Prev/Next 네비게이션
- [x] A.1 `tree_view.py`: `_search_matches`, `_current_match_idx` 상태 추가 + `'search_active'` 태그 등록
- [x] A.2 `tree_view.py`: `search()` — 매치 리스트 저장, idx=0 리셋, `_goto_match(0)` 호출
- [x] A.3 `tree_view.py`: `_goto_match(idx)` 신규 — search_active 이동, see+selection_set
- [x] A.4 `tree_view.py`: `next_match()` / `prev_match()` — wraparound, (current_1based, total) 반환
- [x] A.5 `main_window.py`: ▲/▼ 버튼 + `"N / M"` 카운트 라벨 UI 추가
- [x] A.6 `main_window.py`: `_do_db_search()` — 라벨 형식 변경, 버튼 활성/비활성 연동
- [x] A.7 `main_window.py`: 키 바인딩 — `<Return>`=다음, `<Shift-Return>`=이전, `<F3>`=다음, `<Shift-F3>`=이전
- [ ] A.8 검증: 매치 0/1/N개, wraparound, 검색어 변경 후 idx 리셋, populate 후 클리어

## Phase B — F5: Open DB 서버 폴더 접근 보강
- [x] B.1 `db_extractor.py`: `extract_all_modules()` — `iterdir()` `try/except (PermissionError, OSError)` 추가
- [x] B.2 `db_extractor.py`: `extract_module_parts()` — 경로 접근 권한 에러 처리 (DBExtractor.__init__ PermissionError)
- [x] B.3 `db_extractor.py`: `validate_db_root()` 신규 메서드
- [x] B.4 `db_extractor.py`: `find_db_root_in_subtree(start, max_depth=3)` 신규 메서드
- [x] B.5 `main_window.py`: `open_db()` — `initialdir` 우선순위 로직 추가
- [x] B.6 `main_window.py`: `_load_db_thread()` — 검증→자동정정→안내 분기 추가
- [x] B.7 `main_window.py`: `_on_db_loaded()` — `db_root_path` settings 저장 추가
- [ ] B.8 검증: 정상/누락/권한/한글경로/UNC/한단계위 선택 시나리오

## Phase C — F13: 자동 업데이트 체크
- [x] C.1 `dbmanager-server/init/02_app_releases.sql` 스키마 생성
- [x] C.2 `src/utils/version.py` 신규 — APP_VERSION="1.5.0", parse_version, is_newer
- [x] C.3 `src/core/update_checker.py` 신규 — UpdateChecker.check_async()
- [x] C.4 `src/ui/update_dialog.py` 신규 — UpdateAvailableDialog (일반/강제 모드)
- [x] C.5 `main_window.py`: `__init__` 끝에 비동기 체크 트리거 (온라인 모드만)
- [x] C.6 `main_window.py`: skipped_versions 처리 + `load_settings()` 읽기/쓰기
- [x] C.7 `admin_window.py`: server_settings 탭 하단에 "지금 확인" 버튼
- [ ] C.8 검증: 새버전/없음/오프라인/스키마없음/잘못된버전/skipped/critical 시나리오

## Phase D — F14: Excel 리포트 템플릿 커스터마이징
- [x] D.1 `config/report_template.json` 기본값 파일 생성
- [x] D.2 `src/utils/template_helper.py` 신규 — load/save/validate/apply_placeholders
- [x] D.3 `src/utils/report_generator.py` — `__init__(template=None)` + template 연동
- [x] D.4 `src/ui/report_template_panel.py` 신규 — 편집 UI
- [x] D.5 `admin_window.py` — "리포트 템플릿" 탭 등록
- [x] D.6 미리보기 기능 구현 (더미 데이터 + tempfile + os.startfile)
- [ ] D.7 검증: 로고유무/잘못된색상/잘못된placeholder/모든시트비활성/CoverPage

## Phase E — 문서 / 릴리즈
- [ ] E.1 `docs/CHANGELOG.md` v1.5.0 섹션 추가
- [x] E.2 앱 타이틀 v1.4.0 → v1.5.0 (version.py에서 import)
- [ ] E.3 `사용설명서.md` — 검색 단축키 / Update 다이얼로그 / 리포트 템플릿 섹션

## Phase F — 검증 & 커밋
- [x] F.1 `python -m pytest tests/` — 기존 회귀 통과 (66개 → 99개, 모두 pass)
- [x] F.2 `tests/test_version.py` 작성 + 통과
- [x] F.3 `tests/test_db_extractor_v15.py` 신규 케이스 작성 + 통과
- [x] F.4 `tests/test_update_checker.py` 작성 + 통과
- [x] F.5 `tests/test_template_helper.py` 작성 + 통과
- [ ] F.6 수동 검증 시나리오 (F4/F5/F13/F14 핵심)
- [ ] F.7 EXE 빌드 테스트
- [ ] F.8 main 브랜치 커밋 + push

## 품질 체크
- [x] 에러 처리: 권한/네트워크/파일 없음 케이스 모두 silent fail 또는 사용자 안내
- [x] 보안: settings.json에 비밀번호 저장 없음, UNC 경로 직접 실행 확인
- [x] 기존 API 하위 호환: report_generator 생성자 default=None으로 유지
- [x] 오프라인 모드 동작 확인
