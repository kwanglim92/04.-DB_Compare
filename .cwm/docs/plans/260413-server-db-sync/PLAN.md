# PLAN: 서버 DB 동기화

## 목표
QC Spec 데이터를 사내 PostgreSQL 서버에서 중앙 관리하고, 클라이언트 앱이 자동 동기화하도록 전환한다.
재배포 없이 Spec 추가/수정이 가능해지며, 오프라인/외부 반출 시 로컬 모드로 전환 가능.

## 배경
- 현재: JSON 파일을 EXE에 내장 → Spec 변경마다 재빌드/재배포 필요
- 목표: 서버 DB에 Spec 저장 → 앱 시작 시 동기화 → 공지만으로 업데이트 완료

## 아키텍처

```
[서버 - Docker Compose]              [클라이언트 - EXE]
PostgreSQL:5434  ◄── psycopg2 ──►  SyncManager
pgAdmin:5050                        ├ 앱 시작 시 버전 체크
                                    ├ 변경분 다운로드 → 로컬 캐시
                                    └ 오프라인 폴백
```

## Phase 구성

### Phase 1: 서버 인프라
- Docker Compose 파일 작성 (PostgreSQL 16 + pgAdmin 4)
- DB 스키마 설계 (specs, profiles, versions 테이블)
- 초기 데이터 마이그레이션 스크립트 (JSON → PostgreSQL)

### Phase 2: 클라이언트 동기화 모듈
- `src/core/sync_manager.py` 신규 생성
  - 서버 연결/해제
  - 버전 비교
  - Spec 다운로드 → 로컬 JSON 캐시 저장
  - 오프라인 폴백 로직
- `src/utils/config_helper.py` 수정
  - 로컬 캐시 경로 (AppData) 추가
  - online/offline 모드 분기

### Phase 3: 접속 설정 UI
- 앱 내 서버 설정 다이얼로그
  - Host, Port, DB명, 사용자, 비밀번호 입력
  - 연결 테스트 버튼
  - 접속 정보 암호화 저장
- settings.json에 online/offline 모드 토글

### Phase 4: 통합 및 테스트
- main_window.py에 동기화 플로우 통합
  - 앱 시작 → 서버 연결 시도 → 동기화 → 기존 플로우
  - 상태바에 연결 상태 표시
- 오프라인 모드 전환 테스트
- 외부 반출용 로컬 패키징 테스트

## 기술 결정
- DB 드라이버: psycopg2-binary ≥2.9
- 서버 포트: PostgreSQL 5434, pgAdmin 5050
- 암호화: Python cryptography (Fernet) 또는 keyring
- 로컬 캐시: %APPDATA%/DB_Manager/config/
- Docker: 별도 compose 파일로 기존 프로젝트와 격리

## 제약사항
- 서버 접속 불가 시 반드시 로컬 캐시로 동작해야 함
- 기존 JSON 기반 SpecManager 인터페이스 유지 (하위 호환)
- EXE 빌드 시 psycopg2 포함 필요 (hiddenimports 추가)
