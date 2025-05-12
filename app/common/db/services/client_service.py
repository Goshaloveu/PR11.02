# services/client_service.py
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..repositories import ClientRepository
from ..models_sqlalchemy import Client as ClientSQL
from ..models_pydantic import Client, ClientCreate, ClientUpdate
from ...signal_bus import signalbus
from .password_service import PasswordService # Сервис для хеширования пароля

logger = logging.getLogger(__name__)

class ClientService:
    def __init__(self):
        self.repository = ClientRepository()
        self.password_service = PasswordService() # Нужен для хеширования при создании/обновлении

    def get_client(self, db: Session, client_id: str) -> Optional[Client]:
        logger.debug(f"Service: Getting client id {client_id}")
        db_client = self.repository.get(db, id=client_id)
        return Client.model_validate(db_client) if db_client else None

    def get_clients(self, db: Session, skip: int = 0, limit: int = 100) -> List[Client]:
        logger.debug(f"Service: Getting multiple clients (skip={skip}, limit={limit})")
        db_clients = self.repository.get_multi(db, skip=skip, limit=limit)
        return [Client.model_validate(c) for c in db_clients]

    def get_client_by_username(self, db: Session, username: str) -> Optional[Client]:
        logger.debug(f"Service: Getting client by username {username}")
        db_client = self.repository.get_by_username(db, username=username)
        # Возвращаем Pydantic модель (без хеша)
        return Client.model_validate(db_client) if db_client else None

    def create_client(self, db: Session, client_in: ClientCreate) -> Client:
        logger.info(f"Service: Creating client {client_in.username}")
        # Проверка на существующий username
        existing = self.repository.get_by_username(db, username=client_in.username)
        if existing:
            raise ValueError(f"Username '{client_in.username}' is already taken.")
        # Можно добавить проверку email/phone, если нужно

        try:
            # Хешируем пароль
            hashed_password = self.password_service.get_password_hash(client_in.password)
            # Подготавливаем данные для репозитория
            create_data = client_in.model_dump(exclude={'password'}) # Исключаем пароль
            create_data['hashed_password'] = hashed_password # Добавляем хеш

            # Используем Pydantic модель без пароля для create метода репозитория
            # Репозиторий ожидает CreateSchemaType, но мы передаем словарь
            # Важно: Убедимся, что BaseRepository.create может принимать словарь
            # Передаем словарь напрямую в конструктор SQLAlchemy модели в репозитории
            db_client = self.repository.create(db, obj_in=create_data) # Передаем словарь

            pydantic_client = Client.model_validate(db_client)
            signalbus.client_created.emit(pydantic_client.model_dump())
            return pydantic_client
        except Exception as e:
            logger.error(f"Service Error creating client: {e}")
            signalbus.database_error.emit(f"Ошибка создания клиента: {e}")
            raise

    def update_client(self, db: Session, client_id: str, client_in: ClientUpdate) -> Optional[Client]:
        logger.info(f"Service: Updating client id {client_id}")
        db_client = self.repository.get(db, id=client_id)
        if not db_client:
            logger.warning(f"Client with id {client_id} not found for update.")
            return None

        update_data = client_in.model_dump(exclude_unset=True)

        # Проверка уникальности username при смене
        if "username" in update_data and update_data["username"] != db_client.username:
             existing = self.repository.get_by_username(db, username=update_data["username"])
             if existing:
                 raise ValueError(f"Username '{update_data['username']}' is already taken.")

        # Обновление пароля, если он передан
        if "password" in update_data and update_data["password"]:
            hashed_password = self.password_service.get_password_hash(update_data["password"])
            update_data["hashed_password"] = hashed_password
        # Удаляем поле password из словаря, чтобы не пытаться записать его в БД как есть
        update_data.pop("password", None)

        if not update_data: return Client.model_validate(db_client) # Нет изменений

        try:
            updated_db_client = self.repository.update(db, db_obj=db_client, obj_in=update_data)
            pydantic_client = Client.model_validate(updated_db_client)
            signalbus.client_updated.emit(pydantic_client.model_dump())
            return pydantic_client
        except Exception as e:
             logger.error(f"Service Error updating client {client_id}: {e}")
             signalbus.database_error.emit(f"Ошибка обновления клиента: {e}")
             raise

    def delete_client(self, db: Session, client_id: str) -> bool:
        logger.info(f"Service: Deleting client id {client_id}")
        try:
            deleted_client = self.repository.remove(db, id=client_id)
            if deleted_client:
                signalbus.client_deleted.emit(client_id)
                return True
            logger.warning(f"Client {client_id} not found for deletion.")
            return False
        except Exception as e: # Ловим IntegrityError и другие
            logger.error(f"Service Error deleting client {client_id}: {e}")
            db.rollback() # Явный роллбэк при ошибке удаления
            signalbus.database_error.emit(f"Ошибка удаления клиента {client_id}: {e}")
            raise # Передаем ошибку дальше, чтобы UI мог ее обработать