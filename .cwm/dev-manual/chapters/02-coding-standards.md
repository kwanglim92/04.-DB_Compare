# 02. Coding Standards

## 네이밍 규칙

| 대상 | 스타일 | 예시 |
|------|--------|------|
| 함수/메서드 | snake_case | `load_spec_file()` |
| 변수 | snake_case | `profile_name` |
| 클래스 | PascalCase | `SpecManager` |
| 상수 | UPPER_SNAKE_CASE | `APP_VERSION` |
| 파일명 | snake_case | `config_helper.py` |

## Import 순서

```python
# DO
import sys
import json
from pathlib import Path          # 1. 표준 라이브러리

import customtkinter as ctk       # 2. 서드파티
from openpyxl import Workbook

from src.core.spec_manager import SpecManager  # 3. 로컬 모듈
from src.utils.config_helper import get_config_dir
```

```python
# DON'T
from src.core.spec_manager import SpecManager
import sys
import customtkinter as ctk
import json  # 순서 섞임
```

## 문자열

```python
# DO — f-string 사용
logger.info(f"Loaded {len(profiles)} profiles")
title = f"DB_Manager v{APP_VERSION}"

# DON'T — format() 또는 % 사용
logger.info("Loaded {} profiles".format(len(profiles)))
title = "DB_Manager v%s" % APP_VERSION
```

## 로깅

```python
# DO — 모듈별 logger
import logging
logger = logging.getLogger(__name__)

logger.info(f"Profile loaded: {profile_name}")
logger.error(f"Failed to connect: {e}")

# DON'T — print 또는 root logger
print("Profile loaded")
logging.info("Profile loaded")
```

## Docstring

```python
# DO — 간결한 한줄 설명
def load_spec_file(self, json_path: str) -> bool:
    """Load spec profiles from JSON file"""

# 파라미터가 복잡한 경우만 상세 docstring
def _merge_specs(self, base: Dict, updates: Dict, override_mode: bool = False) -> Dict:
    """
    Merge spec dictionaries recursively

    Args:
        base: Base spec dictionary
        updates: Updates to apply
        override_mode: If True, override matching items. If False, add new items
    """
```

## 들여쓰기

- 4 spaces (탭 사용 금지)

## 타입 힌트

```python
# DO — 함수 시그니처에 타입 힌트
def get_all_profile_names(self) -> List[str]:
def load_profile_with_inheritance(self, profile_name: str) -> Optional[Dict]:

# typing 모듈 사용
from typing import Dict, List, Optional, Any
```
