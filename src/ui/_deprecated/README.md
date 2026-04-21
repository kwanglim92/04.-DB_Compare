# Deprecated UI Modules

이 디렉터리의 모듈들은 **v1.3.0에서 제거**되었습니다. 복구 참조용으로 보존됩니다.

## 이관된 모듈

| 파일 | 대체된 기능 |
|------|------------|
| `profile_manager.py` | `src/ui/admin_window.py` (Admin → Spec 관리 탭) |
| `profile_editor.py` | `src/ui/server_spec_manager.py` 내 `SpecItemDialog` |

## 제거 사유

v1.2에서 Server DB Sync가 도입되면서 `ServerSpecManagerPanel`이 Profile Manager의 모든 기능(CRUD·트리/테이블·검색·Import/Export)을 흡수했습니다. 두 편집 경로가 공존하면 **Single Source of Truth** 원칙이 깨지고 엔지니어 간 Spec 불일치가 발생하므로, v1.3.0부터 서버 편집 경로 하나로 일원화했습니다.

## 관련 문서

- `.cwm/docs/plans/260421-admin-mode-consolidation/`
- `docs/PRD_DB_Manager_v1.1.0.md`
- `docs/CHANGELOG.md`
