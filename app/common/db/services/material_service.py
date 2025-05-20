# services/material_service.py
# Остается как в предыдущем ответе, КРОМЕ ИСПРАВЛЕНИЯ В change_balance
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..repositories import MaterialRepository, MaterialOnOrderRepository
from .. import models_sqlalchemy as models
from ..models_pydantic import Material, MaterialCreate, MaterialUpdate
from ..utils import UUIDUtils
from ...signal_bus import signalBus

logger = logging.getLogger(__name__)

class MaterialService:
    def __init__(self):
        self.repository = MaterialRepository()

    def get_material(self, db: Session, material_id: str) -> Optional[Material]:
        logger.debug(f"Service: Getting material id {material_id}")
        db_mat = self.repository.get(db, id=material_id)
        return Material.model_validate(db_mat) if db_mat else None

    def get_materials(self, db: Session, skip: int = 0, limit: int = 100) -> List[Material]:
        logger.debug(f"Service: Getting multiple materials (skip={skip}, limit={limit})")
        db_mats = self.repository.get_multi(db, skip=skip, limit=limit)
        return [Material.model_validate(m) for m in db_mats]

    def create_material(self, db: Session, material_in: MaterialCreate) -> Material:
        logger.info(f"Service: Creating material type {material_in.type}")
        try:
            db_mat = self.repository.create(db, obj_in=material_in)
            pydantic_mat = Material.model_validate(db_mat)
            signalBus.material_created.emit(pydantic_mat.model_dump())
            return pydantic_mat
        except Exception as e:
            logger.error(f"Service Error creating material: {e}")
            signalBus.database_error.emit(f"Ошибка создания материала: {e}")
            raise

    def update_material(self, db: Session, material_id: str, material_in: MaterialUpdate) -> Optional[Material]:
        logger.info(f"Service: Updating material id {material_id}")
        db_mat = self.repository.get(db, id=material_id)
        if not db_mat: logger.warning(f"Material {material_id} not found"); return None

        update_data = material_in.model_dump(exclude_unset=True)
        if not update_data: return Material.model_validate(db_mat)

        try:
            # Обновляем все поля, включая баланс, если он передан
            updated_db_mat = self.repository.update(db, db_obj=db_mat, obj_in=update_data)

            # Если баланс был обновлен этим вызовом, эмитируем отдельный сигнал
            if 'balance' in update_data:
                signalBus.material_balance_changed.emit(material_id, updated_db_mat.balance)

            pydantic_mat = Material.model_validate(updated_db_mat)
            signalBus.material_updated.emit(pydantic_mat.model_dump())
            return pydantic_mat
        except Exception as e:
            logger.error(f"Service Error updating material {material_id}: {e}")
            signalBus.database_error.emit(f"Ошибка обновления материала: {e}")
            raise

    def change_balance(self, db: Session, material_id: str, quantity_change: int) -> Optional[Material]:
        """ Изменяет баланс материала (списание/приход). Вызывает repository.update_balance """
        logger.info(f"Service: Changing balance for material {material_id} by {quantity_change}")
        if quantity_change == 0:
             logger.warning("Balance change called with zero quantity change.")
             return self.get_material(db, material_id) # Возвращаем текущий объект

        try:
            # Вызываем метод репозитория, который содержит логику атомарного обновления
            updated_db_mat = self.repository.update_balance(db, material_id=material_id, change=quantity_change)
            # Репозиторий сам выбросит ValueError при недостаточном балансе или др. проблемах
            if updated_db_mat:
                pydantic_mat = Material.model_validate(updated_db_mat)
                signalBus.material_balance_changed.emit(material_id, pydantic_mat.balance)
                return pydantic_mat
            else:
                 # Сюда не должны попасть, если репозиторий работает правильно
                 logger.error(f"Service Error: update_balance for material {material_id} returned None unexpectedly.")
                 signalBus.error_occurred.emit(f"Не удалось изменить баланс материала {material_id}.")
                 return None
        except ValueError as ve: # Ловим ошибку недостатка баланса от репозитория
             logger.warning(f"Service Warning changing balance for material {material_id}: {ve}")
             signalBus.error_occurred.emit(f"Не удалось изменить баланс материала {material_id}: {ve}")
             return None # Возвращаем None при ошибке (недостаток и т.п.)
        except Exception as e:
            logger.error(f"Service Error changing balance for material {material_id}: {e}")
            signalBus.database_error.emit(f"Ошибка изменения баланса материала: {e}")
            raise # Передаем другие ошибки выше

    def delete_material(self, db: Session, material_id: str) -> bool:
        logger.info(f"Service: Deleting material id {material_id}")
        try:
            # Проверяем связи с заказами перед удалением
            mat_on_order_repo = MaterialOnOrderRepository()
            links = mat_on_order_repo.find_by_material_id(db, material_id=material_id)
            if links:
                logger.warning(f"Cannot delete material {material_id} as it is used in {len(links)} order(s).")
                signalBus.error_occurred.emit(f"Нельзя удалить материал {material_id}, т.к. он используется в заказах.")
                return False

            deleted = self.repository.remove(db, id=material_id)
            if deleted:
                signalBus.material_deleted.emit(material_id)
                return True
            logger.warning(f"Material {material_id} not found for deletion.")
            return False
        except Exception as e:
            logger.error(f"Service Error deleting material {material_id}: {e}")
            db.rollback()
            signalBus.database_error.emit(f"Ошибка удаления материала {material_id}: {e}")
            raise