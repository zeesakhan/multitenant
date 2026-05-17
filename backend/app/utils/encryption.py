import base64
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from config import get_settings

settings = get_settings()


def _get_fernet() -> Fernet:
    key_bytes = settings.encryption_key.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"health_insurance_platform",
        iterations=100_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
    return Fernet(key)


def encrypt(data: str | dict) -> str:
    """Encrypt a string or dict. Returns base64-encoded ciphertext."""
    if isinstance(data, dict):
        data = json.dumps(data)
    f = _get_fernet()
    return f.encrypt(data.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt ciphertext. Returns plaintext string."""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()


def decrypt_json(ciphertext: str) -> dict:
    """Decrypt ciphertext and parse as JSON."""
    return json.loads(decrypt(ciphertext))
