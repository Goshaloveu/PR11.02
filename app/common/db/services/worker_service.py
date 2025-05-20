# services/worker_service.py
# Аналогично ClientService, но для Worker
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..repositories import WorkerRepository
from ..models_sqlalchemy import Worker as WorkerSQL
from ..models_pydantic import Worker, WorkerCreate, WorkerUpdate
from ...signal_bus import signalBus
from .password_service import PasswordService

logger = logging.getLogger(__name__)

class WorkerService:
    def __init__(self):
        self.repository = WorkerRepository()
        self.password_service = PasswordService()

    def get_worker(self, db: Session, worker_id: str) -> Optional[Worker]:
        logger.debug(f"Service: Getting worker id {worker_id}")
        db_obj = self.repository.get(db, id=worker_id)
        return Worker.model_validate(db_obj) if db_obj else None

    def get_workers(self, db: Session, skip: int = 0, limit: int = 100) -> List[Worker]:
        logger.debug(f"Service: Getting multiple workers (skip={skip}, limit={limit})")
        db_objs = self.repository.get_multi(db, skip=skip, limit=limit)
        return [Worker.model_validate(w) for w in db_objs]

    def get_worker_by_phone(self, db: Session, phone: str) -> Optional[Worker]:
        """Get worker by phone, trying different phone number formats"""
        logger.debug(f"Service: Getting worker by phone {phone}")
        
        # First try direct lookup
        db_obj = self.repository.get_by_phone(db, phone=phone)
        
        # If not found, try alternative formats
        if not db_obj:
            if phone.startswith("+7") and len(phone) > 2:
                # Try without +7 prefix
                alt_phone = phone[2:]  # Get last 10 digits
                logger.debug(f"Worker not found with +7 prefix, trying without: {alt_phone}")
                db_obj = self.repository.get_by_phone(db, phone=alt_phone)
            elif len(phone) == 10 and phone.isdigit():
                # Try with +7 prefix
                alt_phone = "+7" + phone
                logger.debug(f"Worker not found with 10 digits, trying with +7 prefix: {alt_phone}")
                db_obj = self.repository.get_by_phone(db, phone=alt_phone)
                
        return db_obj
        
    def get_worker_by_email(self, db: Session, email: str) -> Optional[Worker]:
        logger.debug(f"Service: Getting worker by email {email}")
        db_obj = self.repository.get_by_email(db, email=email)
        return db_obj

    def create_worker(self, db: Session, worker_in: WorkerCreate) -> Worker:
        logger.info(f"Service: Creating worker with phone {worker_in.phone}")
        
        # Проверка на существующий телефон
        if worker_in.phone:
            existing = self.repository.get_by_phone(db, phone=worker_in.phone)
            if existing:
                raise ValueError(f"Телефон '{worker_in.phone}' уже используется.")
        
        # Проверка на существующий email
        if worker_in.mail:
            existing = self.repository.get_by_email(db, email=worker_in.mail)
            if existing:
                raise ValueError(f"Email '{worker_in.mail}' уже используется.")

        try:
            hashed_password = self.password_service.get_password_hash(worker_in.password)
            create_data = worker_in.model_dump(exclude={'password'})
            create_data['hash_password'] = hashed_password

            db_obj = self.repository.create(db, obj_in=create_data) # Передаем словарь
            
            # Отправляем сигнал с моделью SQLAlchemy
            signalBus.worker_created.emit(db_obj)
            return db_obj
        except Exception as e:
            logger.error(f"Service Error creating worker: {e}")
            signalBus.database_error.emit(f"Ошибка создания работника: {e}")
            raise

    def update_worker(self, db: Session, worker_id: str, worker_in: WorkerUpdate) -> Optional[Worker]:
        logger.info(f"Service: Updating worker id {worker_id}")
        db_obj = self.repository.get(db, id=worker_id)
        if not db_obj: logger.warning(f"Worker {worker_id} not found"); return None

        update_data = worker_in.model_dump(exclude_unset=True)

        # Проверка уникальности телефона при смене
        if "phone" in update_data and update_data["phone"] != db_obj.phone:
            if update_data["phone"]:  # Если телефон не пустой
                existing = self.repository.get_by_phone(db, phone=update_data["phone"])
                if existing and existing.id != worker_id:
                    raise ValueError(f"Телефон '{update_data['phone']}' уже используется.")
                    
        # Проверка уникальности email при смене
        if "mail" in update_data and update_data["mail"] != db_obj.mail:
            if update_data["mail"]:  # Если email не пустой
                existing = self.repository.get_by_email(db, email=update_data["mail"])
                if existing and existing.id != worker_id:
                    raise ValueError(f"Email '{update_data['mail']}' уже используется.")

        if "password" in update_data and update_data["password"]:
            hashed_password = self.password_service.get_password_hash(update_data["password"])
            update_data["hash_password"] = hashed_password
        update_data.pop("password", None)

        if not update_data: return Worker.model_validate(db_obj)

        try:
            updated_db_obj = self.repository.update(db, db_obj=db_obj, obj_in=update_data)
            pydantic_obj = Worker.model_validate(updated_db_obj)
            signalBus.worker_updated.emit(pydantic_obj.model_dump())
            return pydantic_obj
        except Exception as e:
             logger.error(f"Service Error updating worker {worker_id}: {e}")
             signalBus.database_error.emit(f"Ошибка обновления работника: {e}")
             raise

    def delete_worker(self, db: Session, worker_id: str) -> bool:
        logger.info(f"Service: Deleting worker id {worker_id}")
        try:
            deleted = self.repository.remove(db, id=worker_id)
            if deleted:
                signalBus.worker_deleted.emit(worker_id)
                return True
            logger.warning(f"Worker {worker_id} not found for deletion.")
            return False
        except Exception as e:
            logger.error(f"Service Error deleting worker {worker_id}: {e}")
            db.rollback()
            signalBus.database_error.emit(f"Ошибка удаления работника {worker_id}: {e}")
            raise