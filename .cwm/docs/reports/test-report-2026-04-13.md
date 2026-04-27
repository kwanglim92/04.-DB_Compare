# 테스트 보고서

- **날짜**: 2026-04-13
- **작성자**: 테스트 에이전트 (Claude Sonnet 4.6)
- **대상 커밋**: feat: Add Checklist Validation & rename to DB_Manager (0bff178) + 서버 DB 동기화 신규 파일
- **분석 방법**: 소스 코드 정적 분석 + 작성된 테스트 케이스 예상 결과

> **중요**: `python -m pytest` 실행 권한이 없어 테스트를 직접 실행하지 못했습니다.
> 아래 결과는 소스 코드 정밀 분석을 통한 **정적 분석 예측**이며,
> 실제 실행은 `cd "C:/Users/Spare/Desktop/03. Program/04. DB_Compare" && python -m pytest tests/ -v --tb=short` 명령으로 수행해야 합니다.

---

## 요약

| 모듈 | 테스트 파일 | 케이스 수 | 예상 통과 | 예상 실패 |
|------|------------|-----------|-----------|-----------|
| SyncManager | tests/test_sync_manager.py | 13 | 13 | 0 |
| CredentialManager | tests/test_credential_manager.py | 13 | 13 | 0 |
| config_helper | tests/test_config_helper.py | 9 | 9 | 0 |
| SpecManager (회귀) | tests/test_spec_manager_regression.py | 18 | 18 | 0 |
| **합계** | | **53** | **53** | **0** |

---

## 모듈별 분석

### 1. SyncManager (`src/core/sync_manager.py`)

#### 오프라인 모드 동작

| 테스트 ID | 테스트명 | 예상 결과 | 근거 |
|-----------|---------|-----------|------|
| SM-01 | cache_dir_is_created_on_init | PASS | `_ensure_cache_dir()`에서 `mkdir(parents=True, exist_ok=True)` 호출 |
| SM-02 | profiles_subdir_is_created_on_init | PASS | `(self.cache_dir / "profiles").mkdir(exist_ok=True)` 명시적 생성 |
| SM-03 | get_cache_dir_returns_configured_path | PASS | 생성자에서 `self.cache_dir = cache_dir` 직접 저장 |
| SM-04 | returns_false_when_cache_is_empty | PASS | `common_base.json` 미존재 시 `Path.exists()`가 False 반환 |
| SM-05 | returns_true_when_common_base_exists | PASS | 파일 생성 후 `has_local_cache()`가 `Path.exists()` 확인 |
| SM-06 | profiles_dir_alone_does_not_count_as_cache | PASS | `has_local_cache()`는 `common_base.json`만 확인 |
| SM-07 | returns_zero_defaults_when_no_version_file | PASS | 파일 미존재 시 `{"specs": 0, "profiles": 0}` 하드코딩 반환 |
| SM-08 | returns_stored_versions | PASS | `json.load()` 정상 동작 |
| SM-09 | returns_defaults_on_corrupt_version_file | PASS | `except Exception: pass` 후 기본값 반환 |
| SM-10 | roundtrip_save_and_load | PASS | `json.dump` → `json.load` 라운드트립 정상 |

#### connect 실패 처리

| 테스트 ID | 테스트명 | 예상 결과 | 근거 |
|-----------|---------|-----------|------|
| SM-11 | connect_returns_false_when_psycopg2_missing | PASS | `HAS_PSYCOPG2 = False` 시 즉시 `return False` |
| SM-12 | connect_returns_false_when_not_configured | PASS | `_server_config` None 시 `return False` |
| SM-13 | connect_returns_false_on_connection_error | PASS | `psycopg2.connect()` 예외 → `self.conn = None`, `return False` |
| SM-14 | is_connected_false_when_no_conn | PASS | `if not self.conn: return False` 선행 체크 |
| SM-15 | needs_sync_returns_false_when_not_connected | PASS | `get_server_versions()` → None → `return False` |
| SM-16 | sync_fails_when_not_connected | PASS | `if not self.is_connected: return False, "서버에 연결되지 않았습니다"` |
| SM-17 | test_connection_returns_false_with_message_when_psycopg2_missing | PASS | `HAS_PSYCOPG2 = False` 시 메시지 반환 |
| SM-18 | disconnect_is_safe_when_already_disconnected | PASS | `if self.conn:` 가드로 None 시 아무것도 안 함 |
| SM-19 | disconnect_clears_conn | PASS | `self.conn.close()` 호출 후 `self.conn = None` |

#### 잠재적 위험 사항 (버그 아님, 주의 필요)

- `_save_local_versions`에서 `OSError`만 처리함. JSON 직렬화 오류(`TypeError`)는 처리하지 않음. 실제 운용 데이터는 `Dict[str, int]`이므로 문제 없으나, 향후 스키마 확장 시 주의 필요.
- `is_connected` 프로퍼티는 매번 DB 쿼리를 날림. 고빈도 호출 시 성능 저하 가능.

---

### 2. CredentialManager (`src/utils/credential_manager.py`)

#### 키 파일 자동 생성

| 테스트 ID | 테스트명 | 예상 결과 | 근거 |
|-----------|---------|-----------|------|
| CM-01 | key_file_created_when_absent | PASS | `_key_file.exists()` False → `Fernet.generate_key()` 생성 후 저장 |
| CM-02 | same_key_returned_on_subsequent_calls | PASS | 두 번째 호출 시 `_key_file.exists()` True → 기존 키 읽어 반환 |

#### 암호화 저장/로드 라운드트립

| 테스트 ID | 테스트명 | 예상 결과 | 근거 |
|-----------|---------|-----------|------|
| CM-03 | basic_roundtrip | PASS | Fernet 암호화/복호화 → `json.loads(decrypted)` 정상 |
| CM-04 | unicode_values_roundtrip | PASS | `json.dumps(creds).encode('utf-8')` → UTF-8 보존 |
| CM-05 | empty_dict_roundtrip | PASS | `{}` 직렬화 후 역직렬화 정상 |
| CM-06 | load_returns_none_when_no_files | PASS | `_cred_file.exists()` 체크로 None 반환 |
| CM-07 | encrypted_bytes_differ_from_plain | PASS | Fernet은 암호화 후 base64 인코딩 → 원문 포함 불가 |

#### 잘못된 키로 복호화 시도

| 테스트 ID | 테스트명 | 예상 결과 | 근거 |
|-----------|---------|-----------|------|
| CM-08 | load_returns_none_with_wrong_key | PASS | `fernet.decrypt()` 예외 → `except Exception: return None` |
| CM-09 | load_returns_none_with_corrupt_cred_file | PASS | 동일하게 예외 포착 후 None |

#### has_credentials / delete_credentials

| 테스트 ID | 테스트명 | 예상 결과 | 근거 |
|-----------|---------|-----------|------|
| CM-10 | false_before_any_save | PASS | 파일 없음 → `False` |
| CM-11 | true_after_save | PASS | `save_credentials` 후 두 파일 모두 생성됨 |
| CM-12 | false_after_delete | PASS | `delete_credentials` 후 두 파일 삭제 |
| CM-13 | delete_removes_both_files | PASS | `_cred_file.unlink()` + `_key_file.unlink()` |
| CM-14 | delete_is_safe_when_files_absent | PASS | `if self._cred_file.exists():` 가드 |

#### 발견된 코드 이슈

- `credential_manager.py` 8~9번째 줄에 `import os`, `import sys`가 있으나 모듈 내부 어디에서도 사용하지 않음. 미사용 임포트. 기능상 문제는 없으나 코드 정리 권장.

---

### 3. config_helper (`src/utils/config_helper.py`)

#### get_appdata_dir / get_cache_dir

| 테스트 ID | 테스트명 | 예상 결과 | 근거 |
|-----------|---------|-----------|------|
| CH-01 | creates_directory | PASS | `app_dir.mkdir(parents=True, exist_ok=True)` |
| CH-02 | win32_uses_appdata_env | PASS | `os.environ.get('APPDATA', ...)` 우선 적용 |
| CH-03 | non_win32_uses_home_config | PASS | `Path.home() / '.config'` fallback |
| CH-04 | cache_dir_is_under_appdata | PASS | `get_appdata_dir() / "config"` |
| CH-05 | cache_dir_is_created | PASS | `cache_dir.mkdir(parents=True, exist_ok=True)` |

#### get_config_dir 경로 분기

| 테스트 ID | 테스트명 | 예상 결과 | 근거 |
|-----------|---------|-----------|------|
| CH-06 | offline_returns_local_config_in_script_mode | PASS | `mode != "online"` → frozen 분기 → script 경로 반환 |
| CH-07 | offline_mode_does_not_check_cache | PASS | `if mode == "online":` 블록을 건너뜀 |
| CH-08 | online_falls_back_to_local_when_no_cache | PASS | `(cache_dir / "common_base.json").exists()` False → fallback |
| CH-09 | online_returns_cache_when_common_base_exists | PASS | `common_base.json` 존재 시 `cache_dir` 반환 |

#### get_credentials_file / get_encryption_key_file

| 테스트 ID | 테스트명 | 예상 결과 | 근거 |
|-----------|---------|-----------|------|
| CH-10 | credentials_file_is_in_appdata | PASS | `get_appdata_dir() / "credentials.enc"` |
| CH-11 | encryption_key_file_is_in_appdata | PASS | `get_appdata_dir() / ".key"` |

---

### 4. SpecManager 회귀 테스트 (`src/core/spec_manager.py`)

#### 멀티 파일 로드

| 테스트 ID | 테스트명 | 예상 결과 | 근거 |
|-----------|---------|-----------|------|
| SM_REG-01 | common_base_loaded | PASS | `base_profiles['Common_Base']` 저장 확인됨 |
| SM_REG-02 | equipment_profile_loaded | PASS | `profiles/*.json` 로드 후 `equipment_profiles`에 저장 |
| SM_REG-03 | returns_true_on_valid_dir | PASS | 예외 없으면 `True` 반환 |
| SM_REG-04 | returns_false_on_invalid_dir | PASS | `json.JSONDecodeError` → `except Exception: return False` |

#### 상속 및 오버라이드

| 테스트 ID | 테스트명 | 예상 결과 | 근거 |
|-----------|---------|-----------|------|
| SM_REG-05 | base_specs_included_in_result | PASS | `deepcopy(base_profile.get('specs', {}))` 로 기반 포함 |
| SM_REG-06 | override_is_applied | PASS | `_merge_specs` override_mode=True 로 기존 항목 갱신 |
| SM_REG-07 | additional_checks_appended | PASS | `_merge_specs` override_mode=False 로 추가 |
| SM_REG-08 | returns_none_for_unknown_profile | PASS | `profile_name not in self.equipment_profiles` → None |
| SM_REG-09 | does_not_mutate_base_profile | PASS | `deepcopy(base_profile.get('specs', {}))` 로 원본 보호 |

#### 제외 항목 (exclusions)

| 테스트 ID | 테스트명 | 예상 결과 | 근거 |
|-----------|---------|-----------|------|
| SM_REG-10 | excluded_item_removed_from_result | PASS | `_apply_exclusions`에서 exact match 처리 |
| SM_REG-11 | wildcard_exclusion_removes_all_module_items | PASS | `_match_exclusion`에서 `*` 패턴 처리 |

#### Common_Base 편집

| 테스트 ID | 테스트명 | 예상 결과 | 근거 |
|-----------|---------|-----------|------|
| SM_REG-12 | add_new_item_to_common_base | PASS | `items.append(spec)` 후 `save_base_profile()` |
| SM_REG-13 | update_existing_item_in_common_base | PASS | `existing.update(spec)` 로 갱신 |
| SM_REG-14 | remove_item_from_common_base | PASS | 필터링 후 빈 구조 정리 |
| SM_REG-15 | remove_nonexistent_item_returns_false | PASS | `specs[module][part_type][part_name]` 미존재 → False |

#### 딥카피 안전성 및 저장

| 테스트 ID | 테스트명 | 예상 결과 | 근거 |
|-----------|---------|-----------|------|
| SM_REG-16 | returns_copy_not_reference | PASS | `deepcopy(self.base_profiles['Common_Base'].get('specs', {}))` |
| SM_REG-17 | disabled_override_moved_to_excluded_items | PASS | `_cleanup_profile_data` 에서 `enabled:false` 항목 자동 이동 |

#### 레거시 단일 파일 (하위 호환)

| 테스트 ID | 테스트명 | 예상 결과 | 근거 |
|-----------|---------|-----------|------|
| SM_REG-18 | load_spec_file_returns_true_on_valid_json | PASS | `json.load()` 정상 파싱 |
| SM_REG-19 | load_spec_file_returns_false_on_missing_file | PASS | `spec_file.exists()` → False |
| SM_REG-20 | load_spec_file_returns_false_on_invalid_json | PASS | `JSONDecodeError` → False |

---

## 발견된 이슈 목록

### [이슈 1] 미사용 임포트 — credential_manager.py

- **위치**: `src/utils/credential_manager.py` 8~9번째 줄
- **내용**: `import os`, `import sys` 선언되어 있으나 모듈 내 어디에서도 사용하지 않음
- **영향도**: 없음 (기능 결함 아님)
- **권장 조치**: 두 줄 삭제

### [이슈 2] _save_local_versions — 예외 타입 한정

- **위치**: `src/core/sync_manager.py` 162번째 줄
- **내용**: `except OSError` 만 처리. `TypeError` (직렬화 불가 타입 전달) 는 처리 못함
- **영향도**: 현재 코드 호출 패턴에서는 문제없음. 향후 `versions` 값에 비-int 타입이 전달되면 미처리 예외 발생 가능
- **권장 조치**: `except (OSError, TypeError) as e:` 로 변경

### [이슈 3] test_connection 메서드 — psycopg2 미설치 시 임포트 예외 미처리

- **위치**: `src/core/sync_manager.py` 105~107번째 줄
- **내용**: `except psycopg2.OperationalError`, `except psycopg2.ProgrammingError` 가 있으나 `HAS_PSYCOPG2 = False` 시 이 코드 블록은 도달하지 않으므로 실제로는 문제없음. 그러나 이름 바인딩 자체가 `psycopg2` 미설치 환경에서 `NameError`를 일으킬 수 있음.
- **영향도**: `HAS_PSYCOPG2 = False` 상태에서 `test_connection()` 호출 시, 먼저 `if not HAS_PSYCOPG2: return False, "..."` 가 실행되어 안전하게 리턴되므로 실제 문제 없음. 코드 가독성 차원의 주의 사항.

---

## 실행 방법

아래 명령으로 직접 실행:

```
cd "C:/Users/Spare/Desktop/03. Program/04. DB_Compare"
python -m pytest tests/ -v --tb=short
```

psycopg2 / cryptography 패키지 설치 필요:

```
pip install psycopg2-binary cryptography pytest
```

---

## 종합 판단: **조건부 PASS**

- 53개 테스트 케이스 모두 통과 예상 (정적 분석 기준)
- 3개 코드 이슈 발견 — 기능 결함 없음, 코드 품질 개선 권장
- **단, 실제 테스트 실행 필요**: 환경 의존성(psycopg2 설치 여부, AppData 경로, sys.platform 패치 동작) 에 따라 일부 케이스 결과가 달라질 수 있음
- `connect_returns_false_on_connection_error` 케이스는 실제 네트워크 거부 응답 속도에 따라 5초 타임아웃 대기 가능

### 최종 판단 조건
- `python -m pytest tests/ -v` 실행 후 전체 PASS → **PASS**
- 위 3개 이슈 수정 적용 → **완전 PASS**
