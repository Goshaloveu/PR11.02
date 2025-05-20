# services/provider_service.py
# Аналогично, но без логики паролей
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..repositories import ProviderRepository
from ..models_sqlalchemy import Provider as ProviderSQL
from ..models_pydantic import Provider, ProviderCreate, ProviderUpdate
from ...signal_bus import signalBus

logger = logging.getLogger(__name__)

class ProviderService:
    def __init__(self):
        self.repository = ProviderRepository()

    def get_provider(self, db: Session, provider_id: str) -> Optional[Provider]:
        logger.debug(f"Service: Getting provider id {provider_id}")
        db_obj = self.repository.get(db, id=provider_id)
        return Provider.model_validate(db_obj) if db_obj else None

    def get_providers(self, db: Session, skip: int = 0, limit: int = 100) -> List[Provider]:
        logger.debug(f"Service: Getting multiple providers (skip={skip}, limit={limit})")
        db_objs = self.repository.get_multi(db, skip=skip, limit=limit)
        return [Provider.model_validate(p) for p in db_objs]

    def find_provider_by_inn(self, db: Session, inn: str) -> Optional[Provider]:
        logger.debug(f"Service: Finding provider by INN {inn}")
        db_obj = self.repository.find_by_inn(db, inn=inn)
        return Provider.model_validate(db_obj) if db_obj else None

    def create_provider(self, db: Session, provider_in: ProviderCreate) -> Provider:
        logger.info(f"Service: Creating provider {provider_in.name}")
        # Проверка уникальности ИНН
        existing = self.repository.find_by_inn(db, inn=provider_in.inn)
        if existing: raise ValueError(f"Provider with INN '{provider_in.inn}' already exists.")

        try:
            db_obj = self.repository.create(db, obj_in=provider_in) # Pydantic модель напрямую
            pydantic_obj = Provider.model_validate(db_obj)
            signalBus.provider_created.emit(pydantic_obj.model_dump())
            return pydantic_obj
        except Exception as e:
            logger.error(f"Service Error creating provider: {e}")
            signalBus.database_error.emit(f"Ошибка создания поставщика: {e}")
            raise

    def update_provider(self, db: Session, provider_id: str, provider_in: ProviderUpdate) -> Optional[Provider]:
        logger.info(f"Service: Updating provider id {provider_id}")
        db_obj = self.repository.get(db, id=provider_id)
        if not db_obj: logger.warning(f"Provider {provider_id} not found"); return None

        update_data = provider_in.model_dump(exclude_unset=True)
        # Проверка уникальности ИНН при смене
        if "inn" in update_data and update_data["inn"] != db_obj.inn:
             existing = self.repository.find_by_inn(db, inn=update_data["inn"])
             if existing: raise ValueError(f"Provider with INN '{update_data['inn']}' already exists.")

        if not update_data: return Provider.model_validate(db_obj)

        try:
            updated_db_obj = self.repository.update(db, db_obj=db_obj, obj_in=update_data)
            pydantic_obj = Provider.model_validate(updated_db_obj)
            signalBus.provider_updated.emit(pydantic_obj.model_dump())
            return pydantic_obj
        except Exception as e:
             logger.error(f"Service Error updating provider {provider_id}: {e}")
             signalBus.database_error.emit(f"Ошибка обновления поставщика: {e}")
             raise

    def delete_provider(self, db: Session, provider_id: str) -> bool:
        logger.info(f"Service: Deleting provider id {provider_id}")
        try:
            # TODO: Подумать, что делать со связями MaterialProvider?
            # SQLAlchemy с cascade="all, delete-orphan" на Material.providers/Provider.materials
            # НЕ удалит поставщика, если на него ссылаются материалы в mat_provider.
            # Нужно либо сначала удалить связи, либо настроить каскад на ForeignKey в mat_provider.
            # Пока что просто удаляем поставщика.
            deleted = self.repository.remove(db, id=provider_id)
            if deleted:
                signalBus.provider_deleted.emit(provider_id)
                return True
            logger.warning(f"Provider {provider_id} not found for deletion.")
            return False
        except Exception as e: # Ловим IntegrityError
            logger.error(f"Service Error deleting provider {provider_id}: {e}")
            db.rollback()
            signalBus.database_error.emit(f"Ошибка удаления поставщика {provider_id}. Возможно, он связан с материалами.")
            raise