# PLAN: 관리자 모드 통합 (v1.3.0)

## 목표
- Profile Manager와 Server DB의 기능 중복을 해소하고, Spec 편집 경로를 **서버 DB 단일 진입점**으로 일원화한다.
- 서버 접속·Spec 편집을 **비밀번호 보호된 AdminWindow** 하나로 통합하여 생산엔지니어의 오조작을 방지한다.
- Online/Offline 상태는 메인에 표시 전용으로 유지하여 상태 인지성을 확보한다.

## 범위 (In-Scope)
- `src/ui/admin_window.py` 신규 생성 (탭 컨테이너)
- `src/ui/main_window.py` 툴바 리팩터링 (Admin 버튼 단일화)
- `server_settings_dialog.py`, `server_spec_manager.py`의 탭 위젯화 (기능은 보존)
- `profile_manager.py`, `profile_editor.py`를 `src/ui/_deprecated/`로 이동
- 오프라인 모드에서 Spec 관리 탭 **편집 비활성화** (읽기 전용)

## 범위 외 (Out-of-Scope)
- 정식 RBAC/권한 시스템 (v2.0+)
- 감사 로그 (v2.0+)
- Admin 사용자 계정 관리 (단일 패스워드 유지)
- 새로운 Spec 관리 기능 추가 (기존 기능 이관만)

## 설계

### AdminWindow 구조
```
AdminWindow (CTkToplevel)
├── [탭 1: 서버 설정]   → ServerSettingsTab (기존 ServerSettingsDialog 이식)
└── [탭 2: Spec 관리]   → ServerSpecManagerTab (기존 ServerSpecManagerWindow 이식)
```

### 인증 플로우
```
메인 [🔒 Admin] 클릭
  → CTkInputDialog 비밀번호 입력
  → pqc123 일치 시 AdminWindow 오픈
  → 불일치 시 에러 메시지
```

### 비밀번호 관리
- 상수: `src/utils/config_helper.py`에 `ADMIN_PASSWORD = "pqc123"` 정의
- 추후 암호화/환경변수화 대응을 위해 단일 상수로 분리

### 메인 창 툴바 (After)
```
[Open DB] [Profile▼] [Run QC] [Export]              │ ● Online [🔒 Admin] [🌓]
```

## 마이그레이션
- 기존 `config/common_base.json`, `config/profiles/*.json`은 **오프라인 캐시 역할로 유지**
- 오프라인 모드에서 SpecManager는 캐시를 읽기만 함 (쓰기 차단)

## 테스트 전략
- 비밀번호 인증 실패/성공 플로우
- 온라인/오프라인 전환 시 Spec 관리 탭의 편집 가능/불가능 상태 확인
- 기존 Server Sync 기능 회귀 테스트 (66개 테스트 통과)

## 릴리즈
- 버전: **v1.3.0**
- CHANGELOG 업데이트
- PRD 업데이트 (§2.3, §6, §8)
- 사용설명서 업데이트 (Profile Manager 진입 경로 제거, Admin 진입 방법 추가)

## 리스크
| 리스크 | 대응 |
|--------|------|
| 기존 로컬 JSON 데이터 유실 가능성 | `_deprecated/` 이동으로 코드 보존, config 파일은 유지 |
| Admin 비밀번호 노출 | 소스 상수는 제품 배포본 한정, 추후 환경변수/암호화 전환 항목 P2로 등록 |
| 회귀 버그 | v1.2 통합 테스트 재실행, 파일럿 1명 대상 사용 테스트 |
