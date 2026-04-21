# CHECKLIST: 관리자 모드 통합 (v1.3.0)

## Phase 1. AdminWindow 통합 창 구축
- [x] 1.1 `src/ui/admin_window.py` 신규 생성 (CTkToplevel + CTkTabview)
- [x] 1.2 `server_settings_dialog.py` 로직을 `ServerSettingsPanel`로 이식 (CTkFrame)
- [x] 1.3 `server_spec_manager.py` 로직을 `ServerSpecManagerPanel`로 이식 (CTkFrame)
- [x] 1.4 탭 간 연동 — Spec 변경 시 `on_change_callback`으로 상위 MainWindow에 알림

## Phase 2. 메인 창 정리
- [x] 2.1 Profile Manager 버튼 제거
- [x] 2.2 Server DB 버튼 제거
- [x] 2.3 Server 설정 버튼 제거
- [x] 2.4 🔒 Admin 버튼 추가 (상단 툴바 우측)
- [x] 2.5 비밀번호 인증 플로우 구현 (`pqc123`) — `prompt_admin_password()`
- [x] 2.6 Online/Offline 인디케이터 유지 (비-클릭 표시 전용, 포맷 통일)
- [x] 2.7 앱 타이틀 v1.0.0 → v1.3.0

## Phase 3. Profile Manager Deprecation
- [x] 3.1 `src/ui/_deprecated/` 디렉터리 생성
- [x] 3.2 `profile_manager.py` → `_deprecated/`로 이동 (git mv)
- [x] 3.3 `profile_editor.py` → `_deprecated/`로 이동 (git mv)
- [x] 3.4 `main_window.py`에서 해당 import 제거
- [x] 3.5 `_deprecated/README.md` 작성 (이관 사유 기록)

## Phase 4. 오프라인 모드 편집 제어
- [x] 4.1 Spec 관리 탭: 오프라인일 때 추가/편집/삭제/Import 비활성화 (`_edit_buttons` 등록 + `configure(state="disabled")`)
- [x] 4.2 모든 CRUD 메서드에 `if self.read_only: return` 가드 추가 (이중 방어)
- [x] 4.3 오프라인 상태 표시 배너 (탭 상단 오렌지 "⚠ 오프라인 모드 — 읽기 전용")
- [x] 4.4 서버 연결 실패 시 graceful fallback 메시지 (`_render_connection_error`)

## Phase 5. 설정 및 상수
- [x] 5.1 `config_helper.py`에 `ADMIN_PASSWORD = "pqc123"` 추가
- [x] 5.2 기존 `pqclevi`와 구분 — 관리자 전용 패스워드 분리

## Phase 6. 문서 업데이트
- [x] 6.1 `CHANGELOG.md`에 v1.3.0 섹션 추가
- [ ] 6.2 `docs/PRD_DB_Manager_v1.1.0.md` 업데이트 (§2.3 기능, §6 Personas, §8 R)
- [ ] 6.3 `docs/사용설명서.md` 업데이트 (Admin 진입 경로)

## Phase 7. 검증
- [x] 7.1 `python -m py_compile` 전체 성공
- [x] 7.2 모든 핵심 import 경로 검증 (`MainWindow`, `AdminWindow`, `ServerSettingsPanel`, `ServerSpecManagerPanel`)
- [x] 7.3 기존 66개 테스트 회귀 통과
- [ ] 7.4 수동 검증 — 비밀번호 인증 성공/실패 플로우
- [ ] 7.5 수동 검증 — 온라인/오프라인 전환 시 편집 버튼 활성/비활성
- [ ] 7.6 EXE 빌드 테스트

## Phase 8. 커밋
- [ ] 8.1 논리 단위 커밋 (Phase별 또는 기능별)
- [ ] 8.2 main 브랜치 push
