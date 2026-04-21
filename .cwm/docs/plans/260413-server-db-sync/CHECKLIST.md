# CHECKLIST: 서버 DB 동기화

## Phase 1: 서버 인프라
- [x] 1.1 docker-compose.dbmanager.yml 작성 (PostgreSQL 16 + pgAdmin 4)
- [x] 1.2 .env 파일 템플릿 작성 (DB_PASSWORD, PGADMIN_PASSWORD)
- [x] 1.3 DB 스키마 설계 및 init.sql 작성
  - [x] specs 테이블 (common_base 데이터)
  - [x] profiles 테이블 (장비별 프로필)
  - [x] sync_versions 테이블 (버전 관리)
- [x] 1.4 JSON → PostgreSQL 마이그레이션 스크립트 작성
- [x] 1.5 서버 배포 및 초기 데이터 투입 테스트

## Phase 2: 클라이언트 동기화 모듈
- [x] 2.1 src/core/sync_manager.py 생성
  - [x] 서버 연결/해제 (psycopg2 커넥션)
  - [x] 버전 비교 (로컬 vs 서버)
  - [x] Spec 다운로드 → 로컬 JSON 캐시 저장
  - [x] 오프라인 폴백 로직
- [x] 2.2 src/utils/config_helper.py 수정
  - [x] 로컬 캐시 경로 추가 (%APPDATA%/DB_Manager/config/)
  - [x] online/offline 모드 경로 분기
- [x] 2.3 requirements.txt에 psycopg2-binary 추가
- [x] 2.4 PyInstaller spec에 psycopg2 hiddenimports 추가

## Phase 3: 접속 설정 UI
- [x] 3.1 src/ui/server_settings_dialog.py 생성
  - [x] Host, Port, DB, User, Password 입력 폼
  - [x] 연결 테스트 버튼
  - [x] 저장/취소 버튼
- [x] 3.2 접속 정보 암호화 저장 로직 구현 (src/utils/credential_manager.py)
- [x] 3.3 sync mode를 credentials에 포함 (online/offline)
- [x] 3.4 main_window.py 툴바에 "Server" 버튼 + sync 인디케이터 추가

## Phase 4: 통합 및 테스트
- [x] 4.1 앱 시작 플로우에 동기화 통합
  - [x] 시작 → 서버 연결 시도 → 동기화 → 기존 플로우
  - [x] 연결 실패 시 로컬 캐시 폴백 + 알림
- [x] 4.2 상태바에 서버 연결 상태 표시 (Online/Offline 인디케이터)
- [x] 4.3 오프라인 모드 전환 테스트 (통합 테스트 통과)
- [x] 4.4 서버 미설정 상태(기존 사용자) 호환 테스트 (통합 테스트 통과)
- [ ] 4.5 EXE 빌드 및 배포 테스트 (서버 환경 구축 후 수행)
