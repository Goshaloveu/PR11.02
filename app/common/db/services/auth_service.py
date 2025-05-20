# services/auth_service.py
from sqlalchemy.orm import Session
from typing import Optional, Tuple, Union
import logging

from ..repositories import ClientRepository, WorkerRepository
from ..models_sqlalchemy import Client as ClientSQL, Worker as WorkerSQL
from ..models_pydantic import Client, Worker, AuthenticatedUser # Pydantic модели
from .password_service import PasswordService # Импортируем сервис паролей
from ...signal_bus import signalBus

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.client_repo = ClientRepository()
        self.worker_repo = WorkerRepository()
        self.password_service = PasswordService()

    def authenticate(self, db: Session, phone: str, password: str, user_type: Optional[str] = None) -> Optional[AuthenticatedUser]:
        """
        Аутентифицирует пользователя (клиента или работника) по номеру телефона.
        Возвращает AuthenticatedUser (содержащий тип и Pydantic модель) или None.
        
        user_type: определяет тип пользователя ('client' или 'worker') для целевого поиска
        """
        logger.info(f"Auth service: Attempting authentication for phone '{phone}'")
        logger.info(f"DEBUG: phone='{phone}', password='{password}'")  # Отладочный вывод
        user_sql: Optional[Union[ClientSQL, WorkerSQL]] = None
        authenticated_type: Optional[str] = None

        # If user_type is specified, only check that type
        if user_type == "client" or user_type is None:
            # 1. Ищем в таблице клиентов
            client = self.client_repo.get_by_phone(db, phone=phone)
            if client:
                logger.debug(f"Found potential client match for phone '{phone}'")
                # Используем поле hash_password из объекта client для проверки
                logger.debug(f"DEBUG: client hash_password='{client.hash_password}'")  # Отладочный вывод
                if self.password_service.verify_password(password, client.hash_password):
                    logger.info(f"Client with phone '{phone}' authenticated successfully.")
                    user_sql = client
                    authenticated_type = 'client'
                else:
                    logger.warning(f"Invalid password for client with phone '{phone}'.")
                    signalBus.login_failed.emit(f"Неверный пароль для пользователя с телефоном '{phone}'.")
                    return None # Неверный пароль
            else:
                logger.debug(f"No client found with phone '{phone}'")  # Отладочный вывод

        # 2. Если не нашли клиента или пароль не подошел, ищем в работниках
        if not user_sql and (user_type == "worker" or user_type is None):
            worker = self.worker_repo.get_by_phone(db, phone=phone)
            if worker:
                logger.debug(f"Found potential worker match for phone '{phone}'")
                if self.password_service.verify_password(password, worker.hash_password):
                    logger.info(f"Worker with phone '{phone}' authenticated successfully.")
                    user_sql = worker
                    authenticated_type = 'worker'
                else:
                    logger.warning(f"Invalid password for worker with phone '{phone}'.")
                    signalBus.login_failed.emit(f"Неверный пароль для пользователя с телефоном '{phone}'.")
                    return None # Неверный пароль

        # 3. Если нигде не нашли или пароль не подошел
        if not user_sql:
            logger.warning(f"Authentication failed: Phone '{phone}' not found in clients or workers.")
            signalBus.login_failed.emit(f"Пользователь с телефоном '{phone}' не найден.")
            return None

        # 4. Преобразуем в словарь для передачи
        try:
            # Преобразуем SQLAlchemy модель в словарь - временное упрощение
            user_dict = {}
            for column in user_sql.__table__.columns:
                if column.name != 'hash_password':  # Исключаем хеш пароля
                    user_dict[column.name] = getattr(user_sql, column.name)
            
            # Создаем AuthenticatedUser со словарем вместо Pydantic модели
            auth_user_data = AuthenticatedUser(user_type=authenticated_type, user_data=user_dict)
            
            # Отправляем сигнал об успешном входе со словарем данных пользователя
            signalBus.login_successful.emit(authenticated_type, user_dict)
            
            return auth_user_data

        except Exception as e:
            logger.error(f"Error processing user data for authenticated user with phone {phone}: {e}")
            signalBus.login_failed.emit("Ошибка обработки данных пользователя.")
            return None
            
    def verify_password(self, db: Session, phone: str, password: str, is_employee: bool = False) -> bool:
        """
        Проверяет пароль пользователя без полной аутентификации
        """
        logger.debug(f"Auth service: Verifying password for {'worker' if is_employee else 'client'} with phone '{phone}'")
        
        if is_employee:
            user = self.worker_repo.get_by_phone(db, phone=phone)
        else:
            user = self.client_repo.get_by_phone(db, phone=phone)
            
        if not user:
            logger.warning(f"User with phone '{phone}' not found for password verification")
            return False
            
        return self.password_service.verify_password(password, user.hash_password)