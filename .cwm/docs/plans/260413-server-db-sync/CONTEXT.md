# CONTEXT: 서버 DB 동기화

## 왜 이 작업을 하는가
장비별 DB Spec을 추가/수정할 때마다 EXE를 재빌드하여 재배포해야 하는 비효율.
사내 서버 PC(Linux + Docker Compose)가 이미 운영 중이므로, 이를 활용하여 중앙 관리 체계 구축.

## 현재 상태
- SpecManager가 JSON 파일(common_base.json + profiles/*.json) 기반으로 동작
- PyInstaller 빌드 시 config/ 폴더가 _MEIPASS에 내장됨
- config_helper.py가 실행 환경(EXE/스크립트)에 따라 경로 분기

## 서버 PC 환경
- OS: Linux
- 컨테이너: Docker Compose
- 사용 중인 포트:
  - 22 (SSH), 80 (BookStack), 3306 (BookStack DB)
  - 5432 (내부 DB), 5433 (cc_test_db)
  - 8002 (Control Chart), 8003 (NocoDB), 8004 (CC Test)
  - 8080 (WebTest), 3389 (RDP)
- 할당 포트: 5434 (PostgreSQL), 5050 (pgAdmin)

## 핵심 파일
- `src/core/spec_manager.py` — Spec 로드/저장 (JSON 기반), 상속 로직
- `src/utils/config_helper.py` — 경로 분기 (frozen/script)
- `src/ui/main_window.py` — 앱 진입, 설정 로드
- `config/settings.json` — 앱 설정
- `config/common_base.json` — 공통 Spec
- `config/profiles/*.json` — 장비별 프로필

## 주의할 점
- SpecManager의 load_multi_file_config / load_profile_with_inheritance 인터페이스 유지
- 동기화는 JSON 캐시를 갱신하는 방식 → SpecManager는 여전히 JSON을 읽음
- 서버 DB는 "진본(source of truth)", 로컬 JSON은 캐시/오프라인 복사본
- 기존 사용자(서버 미설정)는 현재와 동일하게 로컬 JSON만으로 동작해야 함
