# services/password_service.py
from passlib.context import CryptContext
import logging
from ...config import PASSWORD_CONTEXT_SCHEMES

logger = logging.getLogger(__name__)

class PasswordService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=PASSWORD_CONTEXT_SCHEMES, deprecated="auto")
        logger.info(f"Password context initialized with schemes: {PASSWORD_CONTEXT_SCHEMES}")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """ Проверяет соответствие пароля хешу """
        if not plain_password or not hashed_password: return False
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            # Не логируем сам пароль или хеш
            logger.error(f"Password verification error: {type(e).__name__}")
            return False

    def get_password_hash(self, password: str) -> str:
        """ Генерирует хеш пароля """
        if not password: raise ValueError("Password cannot be empty")
        try:
            return self.pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Password hashing error: {type(e).__name__}")
            raise ValueError("Could not hash password") # Не возвращаем пароль