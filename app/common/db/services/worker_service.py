# services/worker_service.py
# Аналогично ClientService, но для Worker
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..repositories import WorkerRepository
from ..models_sqlalchemy import Worker as WorkerSQL
from ..models_pydantic import Worker, WorkerCreate, WorkerUpdate
from ...signal_bus import signalbus
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

    def get_worker_by_username(self, db: Session, username: str) -> Optional[Worker]:
        logger.debug(f"Service: Getting worker by username {username}")
        db_obj = self.repository.get_by_username(db, username=username)
        return Worker.model_validate(db_obj) if db_obj else None

    def create_worker(self, db: Session, worker_in: WorkerCreate) -> Worker:
        logger.info(f"Service: Creating worker {worker_in.username}")
        existing = self.repository.get_by_username(db, username=worker_in.username)
        if existing: raise ValueError(f"Username '{worker_in.username}' is already taken.")

        try:
            hashed_password = self.password_service.get_password_hash(worker_in.password)
            create_data = worker_in.model_dump(exclude={'password'})
            create_data['hashed_password'] = hashed_password

            db_obj = self.repository.create(db, obj_in=create_data) # Передаем словарь

            pydantic_obj = Worker.model_validate(db_obj)
            signalbus.worker_created.emit(pydantic_obj.model_dump())
            return pydantic_obj
        except Exception as e:
            logger.error(f"Service Error creating worker: {e}")
            signalbus.database_error.emit(f"Ошибка создания работника: {e}")
            raise

    def update_worker(self, db: Session, worker_id: str, worker_in: WorkerUpdate) -> Optional[Worker]:
        logger.info(f"Service: Updating worker id {worker_id}")
        db_obj = self.repository.get(db, id=worker_id)
        if not db_obj: logger.warning(f"Worker {worker_id} not found"); return None

        update_data = worker_in.model_dump(exclude_unset=True)

        if "username" in update_data and update_data["username"] != db_obj.username:
             existing = self.repository.get_by_username(db, username=update_data["username"])
             if existing: raise ValueError(f"Username '{update_data['username']}' is already taken.")

        if "password" in update_data and update_data["password"]:
            hashed_password = self.password_service.get_password_hash(update_data["password"])
            update_data["hashed_password"] = hashed_password
        update_data.pop("password", None)

        if not update_data: return Worker.model_validate(db_obj)

        try:
            updated_db_obj = self.repository.update(db, db_obj=db_obj, obj_in=update_data)
            pydantic_obj = Worker.model_validate(updated_db_obj)
            signalbus.worker_updated.emit(pydantic_obj.model_dump())
            return pydantic_obj
        except Exception as e:
             logger.error(f"Service Error updating worker {worker_id}: {e}")
             signalbus.database_error.emit(f"Ошибка обновления работника: {e}")
             raise

    def delete_worker(self, db: Session, worker_id: str) -> bool:
        logger.info(f"Service: Deleting worker id {worker_id}")
        try:
            deleted = self.repository.remove(db, id=worker_id)
            if deleted:
                signalbus.worker_deleted.emit(worker_id)
                return True
            logger.warning(f"Worker {worker_id} not found for deletion.")
            return False
        except Exception as e:
            logger.error(f"Service Error deleting worker {worker_id}: {e}")
            db.rollback()
            signalbus.database_error.emit(f"Ошибка удаления работника {worker_id}: {e}")
            raise