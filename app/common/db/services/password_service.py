# services/password_service.py
# Временно отключаем хеширование паролей для разработки
#from passlib.context import CryptContext
import logging
#from ...config import PASSWORD_CONTEXT_SCHEMES

logger = logging.getLogger(__name__)

class PasswordService:
    def __init__(self):
        # Временно отключаем CryptContext для разработки
        #self.pwd_context = CryptContext(schemes=PASSWORD_CONTEXT_SCHEMES, deprecated="auto")
        #logger.info(f"Password context initialized with schemes: {PASSWORD_CONTEXT_SCHEMES}")
        logger.info("DEVELOPMENT MODE: Password hashing is disabled!")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """ Проверяет соответствие пароля хешу """
        if not plain_password or not hashed_password: return False
        try:
            # Временное решение - простое сравнение паролей
            return plain_password == hashed_password
        except Exception as e:
            # Не логируем сам пароль или хеш
            logger.error(f"Password verification error: {type(e).__name__}")
            return False

    def get_password_hash(self, password: str) -> str:
        """ Генерирует хеш пароля """
        if not password: raise ValueError("Password cannot be empty")
        try:
            # Временное решение - возвращаем пароль как есть
            return password
        except Exception as e:
            logger.error(f"Password storage error: {type(e).__name__}")
            raise ValueError("Could not store password") # Не возвращаем пароль