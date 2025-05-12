# services/auth_service.py
from sqlalchemy.orm import Session
from typing import Optional, Tuple, Union
import logging

from ..repositories import ClientRepository, WorkerRepository
from ..models_sqlalchemy import Client as ClientSQL, Worker as WorkerSQL
from ..models_pydantic import Client, Worker, AuthenticatedUser # Pydantic модели
from .password_service import PasswordService # Импортируем сервис паролей
from ...signal_bus import signalbus

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.client_repo = ClientRepository()
        self.worker_repo = WorkerRepository()
        self.password_service = PasswordService()

    def authenticate(self, db: Session, username: str, password: str) -> Optional[AuthenticatedUser]:
        """
        Аутентифицирует пользователя (клиента или работника).
        Возвращает AuthenticatedUser (содержащий тип и Pydantic модель) или None.
        """
        logger.info(f"Auth service: Attempting authentication for username '{username}'")
        user_sql: Optional[Union[ClientSQL, WorkerSQL]] = None
        user_type: Optional[str] = None

        # 1. Ищем в таблице клиентов
        client = self.client_repo.get_by_username(db, username=username)
        if client:
            logger.debug(f"Found potential client match for username '{username}'")
            if self.password_service.verify_password(password, client.hashed_password):
                logger.info(f"Client '{username}' authenticated successfully.")
                user_sql = client
                user_type = 'client'
            else:
                logger.warning(f"Invalid password for client '{username}'.")
                signalbus.login_failed.emit(f"Неверный пароль для пользователя '{username}'.")
                return None # Неверный пароль

        # 2. Если не нашли клиента или пароль не подошел, ищем в работниках
        if not user_sql:
            worker = self.worker_repo.get_by_username(db, username=username)
            if worker:
                logger.debug(f"Found potential worker match for username '{username}'")
                if self.password_service.verify_password(password, worker.hashed_password):
                    logger.info(f"Worker '{username}' authenticated successfully.")
                    user_sql = worker
                    user_type = 'worker'
                else:
                    logger.warning(f"Invalid password for worker '{username}'.")
                    signalbus.login_failed.emit(f"Неверный пароль для пользователя '{username}'.")
                    return None # Неверный пароль

        # 3. Если нигде не нашли или пароль не подошел
        if not user_sql:
            logger.warning(f"Authentication failed: Username '{username}' not found in clients or workers.")
            signalbus.login_failed.emit(f"Пользователь '{username}' не найден.")
            return None

        # 4. Преобразуем в Pydantic и возвращаем в обертке AuthenticatedUser
        try:
            if user_type == 'client':
                pydantic_user = Client.model_validate(user_sql)
            elif user_type == 'worker':
                pydantic_user = Worker.model_validate(user_sql)
            else: # На всякий случай
                 logger.error("Internal error: user authenticated but type is unknown.")
                 signalbus.login_failed.emit("Внутренняя ошибка сервера.")
                 return None

            auth_user_data = AuthenticatedUser(user_type=user_type, user_data=pydantic_user)
            signalbus.login_successful.emit(user_type, pydantic_user.model_dump()) # Отправляем сигнал
            return auth_user_data

        except Exception as e:
            logger.error(f"Error creating Pydantic model for authenticated user {username}: {e}")
            signalbus.login_failed.emit("Ошибка обработки данных пользователя.")
            return None