# 06. Testing

## 현재 상태

현재 자동화된 테스트 프레임워크는 미도입 상태. 수동 테스트로 검증 중.

## 수동 테스트 체크리스트

### 기본 기능
- [ ] DB XML 파일 로드 → 트리뷰 정상 표시
- [ ] Profile 선택 → QC 검사 실행 → 결과 정상
- [ ] Excel 리포트 생성 → 파일 열기 정상
- [ ] Profile 생성/편집/삭제 정상 동작

### 서버 동기화 (개발 예정)
- [ ] 서버 설정 입력 → 연결 테스트 성공
- [ ] 앱 시작 시 자동 동기화 → Spec 최신화 확인
- [ ] 서버 접속 불가 시 → 로컬 캐시로 정상 동작
- [ ] 오프라인 모드 전환 → 서버 접속 시도 없이 동작
- [ ] 서버 미설정 상태 → 기존과 동일하게 동작

### EXE 빌드 테스트
- [ ] `pyinstaller DB_Compare_QC_Tool.spec` 빌드 성공
- [ ] EXE 실행 → 모든 기능 정상
- [ ] config 파일 경로 분기 정상 (_MEIPASS / AppData)

## 향후 도입 고려

필요 시 pytest 도입 가능:

```python
# tests/test_spec_manager.py
import pytest
from src.core.spec_manager import SpecManager

def test_load_profile_with_inheritance():
    manager = SpecManager()
    manager.load_multi_file_config(Path("config"))
    result = manager.load_profile_with_inheritance("NX-Wafer")
    assert result is not None
    assert "Dsp" in result

def test_offline_fallback():
    """서버 접속 불가 시 로컬 캐시 사용"""
    sync = SyncManager(host="invalid", port=9999)
    result = sync.sync_specs()
    assert result.used_cache is True
```
