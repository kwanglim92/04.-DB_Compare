# 01. Project Overview

## 프로젝트 정보

- **이름**: DB_Manager (QC Inspection Tool)
- **설명**: DB 파일을 QC Spec과 비교 검사하는 데스크톱 도구
- **기술 스택**: Python 3.11+ / CustomTkinter / PostgreSQL / openpyxl
- **빌드**: PyInstaller → 단일 EXE
- **대상 사용자**: QC 검사 담당자

## 핵심 기능

1. **DB XML 파싱**: 장비 DB 파일(XML)을 파싱하여 트리뷰에 표시
2. **QC Spec 비교 검사**: Common Base + Equipment Profile 상속 구조로 Spec 관리, DB 항목과 비교
3. **Profile 관리**: 장비별 프로필 생성/편집, 상속/오버라이드/제외 지원
4. **Excel 리포트**: Summary, All Items, Failed Items 시트로 구성된 검사 보고서
5. **Checklist Validation**: 체크리스트 기반 추가 검증
6. **서버 DB 동기화**: PostgreSQL 서버와 Spec 데이터 동기화 (개발 예정)

## 디렉토리 구조

```
DB_Manager/
├── main.py                     # 진입점
├── src/
│   ├── constants.py            # 앱 상수, 테마, 색상
│   ├── core/                   # 비즈니스 로직
│   │   ├── xml_parser.py       # XML 파싱
│   │   ├── db_extractor.py     # DB 데이터 추출
│   │   ├── comparator.py       # QC 비교 엔진
│   │   ├── spec_manager.py     # Spec 프로필 관리 (상속 포함)
│   │   └── checklist_validator.py
│   ├── ui/                     # GUI 컴포넌트
│   │   ├── main_window.py      # 메인 윈도우
│   │   ├── tree_view.py        # DB 트리뷰
│   │   ├── profile_manager.py  # 프로필 관리 UI
│   │   ├── profile_editor.py   # 프로필 편집 UI
│   │   ├── spec_dialog.py      # Spec 다이얼로그
│   │   ├── spec_item_editor.py # Spec 항목 편집
│   │   ├── na_review_dialog.py # N/A 리뷰
│   │   └── checklist_report_dialog.py
│   └── utils/                  # 유틸리티
│       ├── config_helper.py    # 경로 분기 (EXE/스크립트)
│       ├── format_helpers.py   # 포맷 헬퍼
│       ├── report_generator.py # Excel 리포트 생성
│       ├── migrate_config.py   # 설정 마이그레이션
│       └── cleanup_config.py   # 설정 정리
├── config/                     # Spec 데이터 (JSON)
│   ├── common_base.json        # 공통 Spec
│   ├── profiles/               # 장비별 프로필
│   └── settings.json           # 앱 설정
├── assets/                     # 아이콘 등 리소스
└── docs/                       # 문서
```

## 실행 방법

```bash
# 개발 모드
python main.py

# EXE 빌드
pyinstaller DB_Compare_QC_Tool.spec
```
