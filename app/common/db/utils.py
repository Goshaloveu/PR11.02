# utils/uuid_utils.py
import re
import uuid
import hashlib
import base64
import os
from typing import Optional

class UUIDUtils:
    """ UUID tool class """
    @staticmethod
    def getUUID() -> str:
        """ generate UUID (version 1 based on host ID and time) """
        # Используем hex для получения строки CHAR(32), а не CHAR(36)
        # Если в БД CHAR(36), нужен uuid.uuid1() без .hex или uuid.uuid4()
        # Т.к. в твоей схеме CHAR(36), будем генерировать стандартный UUID string
        # return uuid.uuid1().hex # Это даст 32 символа
        return str(uuid.uuid4()) # Генерирует случайный UUID v4, стандартный формат 36 символов

def get_password_hash(password: str) -> str:
    """Generate a secure hash for a password"""
    # Generate a random salt
    salt = os.urandom(32)
    
    # Use PBKDF2 with SHA-256
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000  # Number of iterations
    )
    
    # Combine salt and key for storage
    storage = salt + key
    
    # Return as base64 string
    return base64.b64encode(storage).decode('utf-8')

def verify_password(stored_password: str, plain_password: str) -> bool:
    """Verify a password against its stored hash"""
    try:
        # Decode the stored password
        storage = base64.b64decode(stored_password.encode('utf-8'))
        
        # Extract salt (first 32 bytes)
        salt = storage[:32]
        
        # Extract stored key
        stored_key = storage[32:]
        
        # Generate key from plain password with same salt
        key = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt,
            100000  # Same number of iterations
        )
        
        # Compare keys using constant-time comparison
        return hashlib.compare_digest(key, stored_key)
    except Exception:
        return False

def extract_phone_digits(phone: Optional[str]) -> Optional[str]:
    """Extract the last 10 digits from a phone number"""
    if not phone:
        return None
        
    # Remove all non-digit characters
    digits = re.sub(r'[^0-9]', '', phone)
    
    # Return last 10 digits
    return digits[-10:] if len(digits) >= 10 else digits
