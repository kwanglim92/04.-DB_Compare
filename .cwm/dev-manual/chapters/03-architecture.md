# 03. Architecture

## 레이어 구조

```
┌─────────────────────────────────────┐
│              UI Layer               │  src/ui/
│   main_window, tree_view, dialogs   │
├─────────────────────────────────────┤
│            Core Layer               │  src/core/
│  spec_manager, comparator,          │
│  xml_parser, db_extractor,          │
│  checklist_validator, sync_manager  │
├─────────────────────────────────────┤
│           Utils Layer               │  src/utils/
│  config_helper, format_helpers,     │
│  report_generator                   │
├─────────────────────────────────────┤
│         Data / Config               │  config/
│  common_base.json, profiles/,       │
│  settings.json                      │
└─────────────────────────────────────┘
```

## 데이터 흐름

```
DB XML 파일 → xml_parser → db_extractor → 트리뷰 표시
                                ↓
Spec JSON → spec_manager → comparator → QC 결과
                                ↓
                        report_generator → Excel 리포트
```

## Spec 상속 구조

```
Common_Base (common_base.json)
    │
    ├── Equipment Profile A (profiles/A.json)
    │   ├── inherits_from: Common_Base
    │   ├── excluded_items: [...]     ← 제외 항목
    │   ├── overrides: {...}          ← 값 변경
    │   └── additional_checks: {...}  ← 추가 항목
    │
    └── Equipment Profile B (profiles/B.json)
        └── ...
```

`SpecManager.load_profile_with_inheritance()` 처리 순서:
1. Common_Base specs를 deep copy
2. overrides 적용 (기존 항목 값 변경)
3. additional_checks 추가 (새 항목)
4. excluded_items 제거

## 서버 동기화 아키텍처 (개발 예정)

```
[PostgreSQL:5434]          [클라이언트 EXE]
  specs 테이블    ◄────►   SyncManager
  profiles 테이블           ├ 버전 비교
  sync_versions             ├ JSON 캐시 갱신
                            └ 오프라인 폴백
        │
        ▼
  SpecManager는 여전히 JSON을 읽음 (인터페이스 변경 없음)
```

핵심: SyncManager가 서버 → 로컬 JSON 캐시를 갱신하고, SpecManager는 JSON만 읽음.

## 빌드 구조 (PyInstaller)

```
main.py
  ├── src/ → datas로 포함
  ├── customtkinter → collect_all로 포함
  ├── config/ → _MEIPASS에 내장 (현재)
  │             → AppData 캐시로 이전 (서버 동기화 후)
  └── 단일 EXE, console=False, icon=assets/icon.ico
```
