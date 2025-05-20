# services/material_provider_service.py
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..repositories import MaterialProviderRepository, ProviderRepository, MaterialRepository
from ..models_sqlalchemy import MaterialProvider as MatProvSQL
from ..models_pydantic import MaterialProvider, MaterialProviderCreate
from ...signal_bus import signalBus

logger = logging.getLogger(__name__)

class MaterialProviderService:
    def __init__(self):
        self.repository = MaterialProviderRepository()
        # Репозитории для проверки FK
        self.provider_repo = ProviderRepository()
        self.material_repo = MaterialRepository()

    def get_link(self, db: Session, link_id: str) -> Optional[MaterialProvider]:
        logger.debug(f"Service: Getting material-provider link id {link_id}")
        db_obj = self.repository.get(db, id=link_id)
        return MaterialProvider.model_validate(db_obj) if db_obj else None

    def get_links_by_provider(self, db: Session, provider_id: str) -> List[MaterialProvider]:
        logger.debug(f"Service: Getting links for provider {provider_id}")
        db_objs = self.repository.find_by_provider_id(db, provider_id=provider_id)
        return [MaterialProvider.model_validate(link) for link in db_objs]

    def get_links_by_material(self, db: Session, material_id: str) -> List[MaterialProvider]:
        logger.debug(f"Service: Getting links for material {material_id}")
        db_objs = self.repository.find_by_material_id(db, material_id=material_id)
        return [MaterialProvider.model_validate(link) for link in db_objs]

    def link_material_to_provider(self, db: Session, link_in: MaterialProviderCreate) -> MaterialProvider:
        """ Создает связь между материалом и поставщиком """
        provider_id = link_in.provider_id
        material_id = link_in.material_id
        logger.info(f"Service: Linking material {material_id} to provider {provider_id}")

        # Проверка существования поставщика и материала
        if not self.provider_repo.get(db, id=provider_id):
            raise ValueError(f"Provider {provider_id} not found.")
        if not self.material_repo.get(db, id=material_id):
            raise ValueError(f"Material {material_id} not found.")

        # Проверка, не существует ли уже такая связь
        existing = self.repository.get_link(db, provider_id=provider_id, material_id=material_id)
        if existing:
            logger.warning(f"Link between provider {provider_id} and material {material_id} already exists.")
            return MaterialProvider.model_validate(existing) # Возвращаем существующую связь

        try:
            # ID для MaterialProvider генерируется в Pydantic BaseEntity
            db_obj = self.repository.create(db, obj_in=link_in)
            pydantic_obj = MaterialProvider.model_validate(db_obj)
            signalBus.material_linked_to_provider.emit(pydantic_obj.model_dump())
            return pydantic_obj
        except Exception as e:
            logger.error(f"Service Error linking material to provider: {e}")
            signalBus.database_error.emit(f"Ошибка связи материала и поставщика: {e}")
            raise

    def unlink_material_from_provider(self, db: Session, link_id: Optional[str] = None, *, provider_id: Optional[str] = None, material_id: Optional[str] = None) -> bool:
        """ Удаляет связь по ID или по паре provider_id/material_id """
        db_obj_to_delete: Optional[MatProvSQL] = None
        log_msg = ""

        if link_id:
            log_msg = f"link id {link_id}"
            db_obj_to_delete = self.repository.get(db, id=link_id)
        elif provider_id and material_id:
            log_msg = f"provider {provider_id} and material {material_id}"
            db_obj_to_delete = self.repository.get_link(db, provider_id=provider_id, material_id=material_id)
        else:
            raise ValueError("Either link_id or both provider_id and material_id must be provided.")

        logger.info(f"Service: Unlinking material from provider ({log_msg})")

        if not db_obj_to_delete:
             logger.warning(f"Link not found for {log_msg}")
             return False

        link_id_to_emit = db_obj_to_delete.id # Получаем ID перед удалением
        try:
            deleted = self.repository.remove(db, id=link_id_to_emit) # Удаляем по ID
            if deleted:
                signalBus.material_unlinked_from_provider.emit(link_id_to_emit)
                return True
            return False # remove вернул None
        except Exception as e:
            logger.error(f"Service Error unlinking material from provider ({log_msg}): {e}")
            db.rollback()
            signalBus.database_error.emit(f"Ошибка удаления связи материала и поставщика: {e}")
            raise