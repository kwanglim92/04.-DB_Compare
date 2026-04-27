# 05. Security

## DB 접속 정보 관리

### 암호화 저장

서버 접속 정보(host, port, user, password)는 앱 내 설정 UI에서 입력받아 암호화 저장한다.

```python
# DO — 암호화 저장 (cryptography Fernet 또는 keyring)
from cryptography.fernet import Fernet

def save_credentials(self, credentials: dict):
    """접속 정보를 암호화하여 저장"""
    key = self.get_or_create_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(json.dumps(credentials).encode())
    # %APPDATA%/DB_Manager/credentials.enc에 저장

def load_credentials(self) -> dict:
    """암호화된 접속 정보를 복호화하여 반환"""
    key = self.get_or_create_key()
    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted_data)
    return json.loads(decrypted.decode())
```

```python
# DON'T — 평문 저장
settings = {
    "db_host": "192.168.1.100",
    "db_password": "mypassword123"  # 절대 금지
}
json.dump(settings, f)
```

### 규칙

1. **비밀번호는 절대 평문 저장하지 않음**
2. **암호화 키는 사용자 머신별로 생성** (이식 불가)
3. **settings.json에는 접속 정보 저장 금지** — 별도 암호화 파일 사용
4. **연결 테스트 시에만 메모리에 복호화**, 사용 후 즉시 폐기

## Git 보안

```gitignore
# .gitignore에 반드시 포함
config/settings.json    # 로컬 설정
*.enc                   # 암호화된 접속 정보
.env                    # 환경변수
```

## Docker 서버 보안

```yaml
# docker-compose에서 환경변수는 .env 파일로 분리
environment:
  POSTGRES_PASSWORD: ${DB_PASSWORD}  # .env에서 로드
```

- `.env` 파일은 git에 커밋하지 않음
- pgAdmin 접속도 비밀번호 설정 필수
