from cryptography.fernet import Fernet
import os

# load or generate key
_key_path = os.path.join(os.path.dirname(__file__), '.secret.key')


def _get_key():
    if os.path.exists(_key_path):
        with open(_key_path, 'rb') as f:
            return f.read()
    key = Fernet.generate_key()
    with open(_key_path, 'wb') as f:
        f.write(key)
    return key


_fernet = Fernet(_get_key())


def encrypt(value: str) -> str:
    return _fernet.encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    return _fernet.decrypt(token.encode()).decode()
