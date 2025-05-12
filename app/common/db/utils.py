# utils/uuid_utils.py
import uuid

class UUIDUtils:
    """ UUID tool class """
    @staticmethod
    def getUUID():
        """ generate UUID (version 1 based on host ID and time) """
        # Используем hex для получения строки CHAR(32), а не CHAR(36)
        # Если в БД CHAR(36), нужен uuid.uuid1() без .hex или uuid.uuid4()
        # Т.к. в твоей схеме CHAR(36), будем генерировать стандартный UUID string
        # return uuid.uuid1().hex # Это даст 32 символа
        return str(uuid.uuid4()) # Генерирует случайный UUID v4, стандартный формат 36 символов
