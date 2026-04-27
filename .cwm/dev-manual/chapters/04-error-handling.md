# 04. Error Handling

## 기본 패턴

```python
# DO — try/except + logger.error + 반환값
def load_spec_file(self, json_path: str) -> bool:
    """Load spec profiles from JSON file"""
    spec_file = Path(json_path)

    if not spec_file.exists():
        self.logger.error(f"Spec file not found: {json_path}")
        return False

    try:
        with open(spec_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return True
    except json.JSONDecodeError as e:
        self.logger.error(f"Failed to parse JSON: {e}")
        return False
    except Exception as e:
        self.logger.error(f"Error loading spec file: {e}")
        return False
```

```python
# DON'T — 예외 무시, bare except
try:
    data = json.load(f)
except:
    pass
```

## 규칙

1. **구체적 예외 먼저** → 일반 Exception은 마지막 폴백
2. **반환값으로 성공/실패 전달** — bool 또는 Optional
3. **logger.error에 원인 포함** — `f"메시지: {e}"`
4. **사용자에게 보여줄 에러는 messagebox** — 내부 에러는 logger만

## UI 에러 표시

```python
# DO — 사용자 친화적 메시지
from tkinter import messagebox

try:
    self.load_data()
except Exception as e:
    logger.error(f"Data load failed: {e}")
    messagebox.showerror("오류", "데이터를 불러올 수 없습니다.")
```

## 서버 연결 에러 처리 (예정)

```python
# 서버 연결 실패 시 로컬 캐시 폴백
def sync_specs(self):
    try:
        self.connect_to_server()
        self.download_updates()
    except ConnectionError as e:
        logger.warning(f"Server unavailable, using local cache: {e}")
        self.use_local_cache()
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        self.use_local_cache()
```

## 파일 I/O

```python
# DO — encoding 명시, Path 사용
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# DON'T — encoding 누락
with open(file_path, 'r') as f:
    data = json.load(f)
```
