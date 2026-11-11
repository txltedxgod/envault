import os
from functools import lru_cache
from pathlib import Path

from cryptography.fernet import Fernet

_DEFAULT_KEY_PATH = Path(__file__).resolve().parent / '.secret.key'


def _load_or_create_key() -> bytes:
    env_key = os.getenv('ENVAULT_SECRET_KEY', '').strip()
    if env_key:
        return env_key.encode('utf-8')

    key_path = Path(os.getenv('ENVAULT_KEY_PATH', str(_DEFAULT_KEY_PATH)))
    if key_path.exists():
        return key_path.read_bytes().strip()

    key = Fernet.generate_key()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_bytes(key)
    try:
        os.chmod(key_path, 0o600)
    except OSError:
        pass
    return key


@lru_cache(maxsize=1)
def get_fernet() -> Fernet:
    return Fernet(_load_or_create_key())


def reset_cipher() -> None:
    get_fernet.cache_clear()


def encrypt(value: str) -> str:
    return get_fernet().encrypt(value.encode('utf-8')).decode('utf-8')


def decrypt(token: str) -> str:
    return get_fernet().decrypt(token.encode('utf-8')).decode('utf-8')
