import os
import base64
import hashlib
from typing import Optional
from sqlalchemy.orm import Session
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import bcrypt
from backend.models import SystemConfig

# Global variable to store the derived key in memory
_ENCRYPTION_KEY: Optional[bytes] = None

def get_encryption_key() -> Optional[bytes]:
    return _ENCRYPTION_KEY

def clear_encryption_key():
    global _ENCRYPTION_KEY
    _ENCRYPTION_KEY = None

def is_vault_unlocked() -> bool:
    return _ENCRYPTION_KEY is not None

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def initialize_vault(db: Session, password: str):
    """
    Initialize the vault with a master password.
    Generates a salt, derives the key, and stores the salt and password hash.
    """
    salt = os.urandom(16)
    salt_b64 = base64.b64encode(salt).decode('utf-8')
    # Use bcrypt directly
    password_bytes = password.encode('utf-8')
    salt_bcrypt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt_bcrypt).decode('utf-8')
    
    # Store salt and hash
    db.merge(SystemConfig(key="master_salt", value=salt_b64))
    db.merge(SystemConfig(key="master_password_hash", value=password_hash))
    db.commit()
    
    # Set the key in memory
    global _ENCRYPTION_KEY
    _ENCRYPTION_KEY = derive_key(password, salt)

def unlock_vault(db: Session, password: str) -> bool:
    """
    Unlock the vault with the master password.
    Verifies the password and derives the key.
    """
    salt_entry = db.query(SystemConfig).filter(SystemConfig.key == "master_salt").first()
    hash_entry = db.query(SystemConfig).filter(SystemConfig.key == "master_password_hash").first()
    
    if not salt_entry or not hash_entry:
        return False
        
    try:
        password_bytes = password.encode('utf-8')
        hash_bytes = hash_entry.value.encode('utf-8')
        if not bcrypt.checkpw(password_bytes, hash_bytes):
            return False
    except Exception:
        return False
        
    salt = base64.b64decode(salt_entry.value)
    global _ENCRYPTION_KEY
    _ENCRYPTION_KEY = derive_key(password, salt)
    return True

def encrypt_value(value: str) -> str:
    """
    Encrypt a string value using AES-256-GCM.
    Returns base64 encoded ciphertext (nonce + ciphertext).
    """
    if not _ENCRYPTION_KEY:
        raise ValueError("Vault is locked")
        
    aesgcm = AESGCM(_ENCRYPTION_KEY)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, value.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode('utf-8')

def decrypt_value(value_b64: str) -> str:
    """
    Decrypt a base64 encoded ciphertext.
    """
    if not _ENCRYPTION_KEY:
        raise ValueError("Vault is locked")
        
    try:
        data = base64.b64decode(value_b64)
        nonce = data[:12]
        ciphertext = data[12:]
        aesgcm = AESGCM(_ENCRYPTION_KEY)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')
    except Exception:
        return "[Decryption Failed]"
