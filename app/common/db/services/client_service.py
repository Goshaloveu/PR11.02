# services/client_service.py
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from uuid import uuid4

from ..repositories import ClientRepository
from ..models_sqlalchemy import Client as ClientSQL
from ..models_pydantic import Client, ClientCreate, ClientUpdate
from ...signal_bus import signalBus
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

    def get_client_by_phone(self, db: Session, phone: str) -> Optional[Client]:
        """Get client by phone, trying different phone number formats"""
        logger.debug(f"Service: Getting client by phone {phone}")
        
        # First try direct lookup
        db_client = self.repository.get_by_phone(db, phone=phone)
        
        # If not found, try alternative formats
        if not db_client:
            if phone.startswith("+7") and len(phone) > 2:
                # Try without +7 prefix
                alt_phone = phone[2:]  # Get last 10 digits
                logger.debug(f"Client not found with +7 prefix, trying without: {alt_phone}")
                db_client = self.repository.get_by_phone(db, phone=alt_phone)
            elif len(phone) == 10 and phone.isdigit():
                # Try with +7 prefix
                alt_phone = "+7" + phone
                logger.debug(f"Client not found with 10 digits, trying with +7 prefix: {alt_phone}")
                db_client = self.repository.get_by_phone(db, phone=alt_phone)
                
        # Возвращаем SQLAlchemy модель напрямую, без преобразования в Pydantic
        return db_client
        
    def get_client_by_email(self, db: Session, email: str) -> Optional[Client]:
        logger.debug(f"Service: Getting client by email {email}")
        db_client = self.repository.get_by_email(db, email=email)
        # Возвращаем SQLAlchemy модель напрямую, без преобразования в Pydantic
        return db_client

    def create_client(self, db: Session, client_in: ClientCreate) -> Client:
        """Create new client"""
        try:
            print(f"ClientService creating client with data: {client_in.model_dump()}")
            
            # Create client with pydantic model
            obj_in = client_in.model_dump()
            
            # Set ID explicitly - UUID as string
            obj_in['id'] = str(uuid4())
            print(f"Set client ID to: {obj_in['id']}")
            
            print(f"Client data after processing: {obj_in}")
            
            # Extract password for hashing
            password = obj_in.pop("password")
            print(f"Password extracted: {password}")
            
            # Hash password
            hash_password = self.password_service.get_password_hash(password)
            print(f"Password hashed successfully")
            
            # Create DB model
            print(f"Creating client model with hash_password length: {len(hash_password)}")
            db_obj = ClientSQL(**obj_in, hash_password=hash_password)
            print(f"Client model created successfully")
            
            # Add to DB
            db.add(db_obj)
            db.commit()  # Commit immediately
            db.refresh(db_obj)
            print(f"Client saved to database with ID: {db_obj.id}")
            
            return Client.model_validate(db_obj)
        except Exception as e:
            print(f"Error in create_client: {str(e)}")
            db.rollback()
            logger.error(f"Service Error creating client: {e}")
            # Формируем читаемое сообщение об ошибке
            raise e

    def update_client(self, db: Session, client_id: str, client_in: ClientUpdate) -> Optional[Client]:
        logger.info(f"Service: Updating client id {client_id}")
        db_client = self.repository.get(db, id=client_id)
        if not db_client:
            logger.warning(f"Client with id {client_id} not found for update.")
            return None

        update_data = client_in.model_dump(exclude_unset=True)

        # Проверка уникальности телефона при смене
        if "phone" in update_data and update_data["phone"] != db_client.phone:
            if update_data["phone"]:  # Если телефон не пустой
                existing = self.repository.get_by_phone(db, phone=update_data["phone"])
                if existing and existing.id != client_id:
                    raise ValueError(f"Телефон '{update_data['phone']}' уже используется.")
                    
        # Проверка уникальности email при смене
        if "mail" in update_data and update_data["mail"] != db_client.mail:
            if update_data["mail"]:  # Если email не пустой
                existing = self.repository.get_by_email(db, email=update_data["mail"])
                if existing and existing.id != client_id:
                    raise ValueError(f"Email '{update_data['mail']}' уже используется.")

        # Обновление пароля, если он передан
        if "password" in update_data and update_data["password"]:
            hashed_password = self.password_service.get_password_hash(update_data["password"])
            update_data["hash_password"] = hashed_password
        # Удаляем поле password из словаря, чтобы не пытаться записать его в БД как есть
        update_data.pop("password", None)

        if not update_data: return Client.model_validate(db_client) # Нет изменений

        try:
            updated_db_client = self.repository.update(db, db_obj=db_client, obj_in=update_data)
            pydantic_client = Client.model_validate(updated_db_client)
            signalBus.client_updated.emit(pydantic_client.model_dump())
            return pydantic_client
        except Exception as e:
             logger.error(f"Service Error updating client {client_id}: {e}")
             signalBus.database_error.emit(f"Ошибка обновления клиента: {e}")
             raise

    def delete_client(self, db: Session, client_id: str) -> bool:
        logger.info(f"Service: Deleting client id {client_id}")
        try:
            deleted_client = self.repository.remove(db, id=client_id)
            if deleted_client:
                signalBus.client_deleted.emit(client_id)
                return True
            logger.warning(f"Client {client_id} not found for deletion.")
            return False
        except Exception as e: # Ловим IntegrityError и другие
            logger.error(f"Service Error deleting client {client_id}: {e}")
            db.rollback() # Явный роллбэк при ошибке удаления
            signalBus.database_error.emit(f"Ошибка удаления клиента {client_id}: {e}")
            raise # Передаем ошибку дальше, чтобы UI мог ее обработать