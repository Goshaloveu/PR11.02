# repositories.py
from typing import List, Optional, Type, TypeVar, Generic, Dict, Any
from sqlalchemy.orm import Session, joinedload, selectinload, subqueryload
from sqlalchemy import select, update as sql_update, delete as sql_delete, func, case, literal_column, and_, or_
from pydantic import BaseModel as PydanticBaseModel
import logging
from datetime import datetime

from .database import Base as SQLAlchemyBaseModel
from .models_pydantic import BaseEntity as PydanticBaseEntity
from .utils import UUIDUtils # Локальный импорт
from ...common.config import config

logger = logging.getLogger(__name__)

SQLAlchemyModelType = TypeVar("SQLAlchemyModelType", bound=SQLAlchemyBaseModel)
PydanticSchemaType = TypeVar("PydanticSchemaType", bound=PydanticBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=PydanticBaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=PydanticBaseModel)

class BaseRepository(Generic[SQLAlchemyModelType, CreateSchemaType, UpdateSchemaType]):
    """ Базовый класс репозитория с CRUD операциями (без изменений) """
    def __init__(self, model: Type[SQLAlchemyModelType]): self._model = model
    def _get_session(self, db: Session):
        if db is None: raise ValueError("Database session is required")
        return db
    def get(self, db: Session, id: str) -> Optional[SQLAlchemyModelType]:
        statement = select(self._model).where(self._model.id == id)
        try: return db.execute(statement).scalar_one_or_none()
        except Exception as e: logger.error(f"Repo Error getting {self._model.__name__} by id {id}: {e}"); db.rollback(); return None
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[SQLAlchemyModelType]:
        statement = select(self._model).offset(skip).limit(limit)
        try: return db.execute(statement).scalars().all()
        except Exception as e: logger.error(f"Repo Error getting multiple {self._model.__name__}: {e}"); db.rollback(); return []
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> SQLAlchemyModelType:
        obj_in_data = obj_in.model_dump()
        if 'id_' in obj_in_data: obj_in_data['id'] = obj_in_data.pop('id_')
        if 'id' not in obj_in_data or not obj_in_data['id']: # Если ID не пришел из Pydantic
            obj_in_data['id'] = UUIDUtils.getUUID()

        db_obj = self._model(**obj_in_data)
        try:
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Repo: Created {self._model.__name__} with id {db_obj.id}")
            return db_obj
        except Exception as e: logger.error(f"Repo Error creating {self._model.__name__}: {e}"); db.rollback(); raise
    def update(self, db: Session, *, db_obj: SQLAlchemyModelType, obj_in: UpdateSchemaType | Dict[str, Any]) -> SQLAlchemyModelType:
        if isinstance(obj_in, PydanticBaseModel): update_data = obj_in.model_dump(exclude_unset=True)
        else: update_data = obj_in
        if not update_data: logger.warning(f"Repo: Update called for {self._model.__name__} id {db_obj.id} with no data."); return db_obj
        for field, value in update_data.items():
            if hasattr(db_obj, field): setattr(db_obj, field, value)
            else: logger.warning(f"Repo: Field '{field}' not found in {self._model.__name__} during update.")
        try:
            db.add(db_obj); db.commit(); db.refresh(db_obj)
            logger.info(f"Repo: Updated {self._model.__name__} with id {db_obj.id}")
            return db_obj
        except Exception as e: logger.error(f"Repo Error updating {self._model.__name__} id {db_obj.id}: {e}"); db.rollback(); raise
    def remove(self, db: Session, *, id: str) -> Optional[SQLAlchemyModelType]:
        obj = self.get(db, id=id)
        if obj:
            try:
                db.delete(obj); db.commit()
                logger.info(f"Repo: Deleted {self._model.__name__} with id {id}")
                return obj
            except Exception as e: logger.error(f"Repo Error deleting {self._model.__name__} id {id}: {e}"); db.rollback(); raise
        else: logger.warning(f"Repo: Delete failed. {self._model.__name__} with id {id} not found."); return None

# --- Конкретные репозитории ---
from .models_sqlalchemy import Client, Order, Worker, Provider, Material, MaterialOnOrder, MaterialProvider
from .models_pydantic import (
    ClientCreate, ClientUpdate, OrderCreate, OrderUpdate, WorkerCreate, WorkerUpdate,
    ProviderCreate, ProviderUpdate, MaterialCreate, MaterialUpdate,
    MaterialOnOrderCreate, MaterialOnOrderUpdate, MaterialProviderCreate, MaterialProviderUpdate,
    OrderStatus
)

class ClientRepository(BaseRepository[Client, ClientCreate, ClientUpdate]):
    def __init__(self): super().__init__(Client)
    def find_by_phone_or_mail(self, db: Session, *, phone: Optional[str] = None, email: Optional[str] = None) -> List[Client]:
        # ... (реализация как раньше) ...
        if not phone and not email: return []
        statement = select(self._model)
        conditions = []
        if phone: conditions.append(self._model.phone == phone)
        if email: conditions.append(self._model.mail == email)
        if conditions:
             from sqlalchemy import or_
             statement = statement.where(or_(*conditions))
        else: return [] # Не ищем, если нет критериев
        try: return db.execute(statement).scalars().all()
        except Exception as e: logger.error(f"Repo Error finding client by phone/email: {e}"); db.rollback(); return []

    def get_by_phone(self, db: Session, phone: str) -> Optional[Client]:
        """ Найти клиента по номеру телефона """
        statement = select(self._model).where(self._model.phone == phone)
        try: return db.execute(statement).scalar_one_or_none()
        except Exception as e: logger.error(f"Repo Error getting client by phone {phone}: {e}"); db.rollback(); return None

    def get_by_email(self, db: Session, email: str) -> Optional[Client]:
        """ Найти клиента по email """
        statement = select(self._model).where(func.lower(self._model.mail) == func.lower(email))
        try: return db.execute(statement).scalar_one_or_none()
        except Exception as e: logger.error(f"Repo Error getting client by email {email}: {e}"); db.rollback(); return None

class WorkerRepository(BaseRepository[Worker, WorkerCreate, WorkerUpdate]):
    def __init__(self): super().__init__(Worker)

    def get_by_phone(self, db: Session, phone: str) -> Optional[Worker]:
        """ Найти работника по номеру телефона """
        statement = select(self._model).where(self._model.phone == phone)
        try: return db.execute(statement).scalar_one_or_none()
        except Exception as e: logger.error(f"Repo Error getting worker by phone {phone}: {e}"); db.rollback(); return None

    def get_by_email(self, db: Session, email: str) -> Optional[Worker]:
        """ Найти работника по email """
        statement = select(self._model).where(func.lower(self._model.mail) == func.lower(email))
        try: return db.execute(statement).scalar_one_or_none()
        except Exception as e: logger.error(f"Repo Error getting worker by email {email}: {e}"); db.rollback(); return None

class ProviderRepository(BaseRepository[Provider, ProviderCreate, ProviderUpdate]):
    def __init__(self): super().__init__(Provider)
    def find_by_inn(self, db: Session, inn: str) -> Optional[Provider]:
        statement = select(self._model).where(self._model.inn == inn)
        try: return db.execute(statement).scalar_one_or_none()
        except Exception as e: logger.error(f"Repo Error finding provider by INN {inn}: {e}"); db.rollback(); return None

class MaterialRepository(BaseRepository[Material, MaterialCreate, MaterialUpdate]):
    def __init__(self): super().__init__(Material)
    def update_balance(self, db: Session, material_id: str, change: int) -> Optional[Material]:
        # ... (реализация как раньше) ...
        update_statement = (
            sql_update(self._model)
            .where(self._model.id == material_id)
            .where(self._model.balance + change >= 0)
            .values(balance=self._model.balance + change)
            #.returning(self._model) # Убираем, т.к. в MySQL может не работать как ожидалось
        )
        try:
            update_result = db.execute(update_statement)
            if update_result.rowcount == 0:
                db.rollback()
                logger.warning(f"Repo: Failed to update balance for material {material_id} (maybe balance < {-change}?)")
                # Получаем текущий объект, чтобы проверить причину
                current_obj = self.get(db, material_id)
                if current_obj and current_obj.balance + change < 0:
                    raise ValueError(f"Insufficient balance for material {current_obj.type}")
                else: # Другая причина (например, ID не найден)
                    raise ValueError(f"Material with ID {material_id} not found or other error.")
            db.commit()
            updated_obj = self.get(db, material_id) # Получаем после коммита
            logger.info(f"Repo: Updated balance for material {material_id} by {change}. New balance: {updated_obj.balance if updated_obj else 'N/A'}")
            return updated_obj
        except Exception as e: logger.error(f"Repo Error updating balance for material {material_id}: {e}"); db.rollback(); raise # Передаем ошибку выше

class OrderRepository(BaseRepository[Order, OrderCreate, OrderUpdate]):
    def __init__(self): super().__init__(Order)
    def find_by_status(self, db: Session, status: OrderStatus) -> List[Order]:
        # ... (реализация как раньше) ...
        statement = select(self._model).where(self._model.status == status)
        try: return db.execute(statement).scalars().all()
        except Exception as e: logger.error(f"Repo Error finding orders by status {status.value}: {e}"); db.rollback(); return []
    def find_by_client(self, db: Session, client_id: str) -> List[Order]:
        # ... (реализация как раньше) ...
        statement = select(self._model).where(self._model.client_id == client_id)
        try: return db.execute(statement).scalars().all()
        except Exception as e: logger.error(f"Repo Error finding orders by client {client_id}: {e}"); db.rollback(); return []
    def find_by_worker(self, db: Session, worker_id: str) -> List[Order]:
        statement = select(self._model).where(self._model.worker_id == worker_id)
        try: return db.execute(statement).scalars().all()
        except Exception as e: logger.error(f"Repo Error finding orders by worker {worker_id}: {e}"); db.rollback(); return []
    
    def find_with_filters(self, db: Session, filters: Dict[str, Any], date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> List[Order]:
        """Find orders with multiple filters"""
        statement = select(self._model)
        
        # Apply all filters
        for field, value in filters.items():
            statement = statement.where(getattr(self._model, field) == value)
            
        # Apply date range if provided
        if date_from:
            statement = statement.where(self._model.date >= date_from)
        if date_to:
            statement = statement.where(self._model.date <= date_to)
            
        try:
            return db.execute(statement).scalars().all()
        except Exception as e:
            logger.error(f"Repo Error finding orders with filters {filters}: {e}")
            db.rollback()
            return []
            
    def count_with_filters(self, db: Session, filters: Dict[str, Any], date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> int:
        """Count orders with multiple filters"""
        from sqlalchemy import func
        statement = select(func.count()).select_from(self._model)
        
        # Apply all filters
        for field, value in filters.items():
            statement = statement.where(getattr(self._model, field) == value)
            
        # Apply date range if provided
        if date_from:
            statement = statement.where(self._model.date >= date_from)
        if date_to:
            statement = statement.where(self._model.date <= date_to)
            
        try:
            return db.execute(statement).scalar() or 0
        except Exception as e:
            logger.error(f"Repo Error counting orders with filters {filters}: {e}")
            db.rollback()
            return 0

class MaterialOnOrderRepository(BaseRepository[MaterialOnOrder, MaterialOnOrderCreate, MaterialOnOrderUpdate]):
    def __init__(self): super().__init__(MaterialOnOrder)
    def find_by_order_id(self, db: Session, order_id: str) -> List[MaterialOnOrder]:
        # ... (реализация как раньше) ...
        statement = select(self._model).where(self._model.order_id == order_id)
        try: return db.execute(statement).scalars().all()
        except Exception as e: logger.error(f"Repo Error finding MatOnOrder by order_id {order_id}: {e}"); db.rollback(); return []
    def find_by_material_id(self, db: Session, material_id: str) -> List[MaterialOnOrder]:
        statement = select(self._model).where(self._model.material_id == material_id)
        try: return db.execute(statement).scalars().all()
        except Exception as e: logger.error(f"Repo Error finding MatOnOrder by material_id {material_id}: {e}"); db.rollback(); return []

class MaterialProviderRepository(BaseRepository[MaterialProvider, MaterialProviderCreate, MaterialProviderUpdate]):
    def __init__(self): super().__init__(MaterialProvider)
    def find_by_provider_id(self, db: Session, provider_id: str) -> List[MaterialProvider]:
        statement = select(self._model).where(self._model.provider_id == provider_id)
        try: return db.execute(statement).scalars().all()
        except Exception as e: logger.error(f"Repo Error finding MatProv by provider_id {provider_id}: {e}"); db.rollback(); return []
    def find_by_material_id(self, db: Session, material_id: str) -> List[MaterialProvider]:
        statement = select(self._model).where(self._model.material_id == material_id)
        try: return db.execute(statement).scalars().all()
        except Exception as e: logger.error(f"Repo Error finding MatProv by material_id {material_id}: {e}"); db.rollback(); return []
    def get_link(self, db: Session, provider_id: str, material_id: str) -> Optional[MaterialProvider]:
         statement = select(self._model).where(
             self._model.provider_id == provider_id,
             self._model.material_id == material_id
         )
         try: return db.execute(statement).scalar_one_or_none()
         except Exception as e: logger.error(f"Repo Error getting MatProv link: {e}"); db.rollback(); return None