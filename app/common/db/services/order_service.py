# services/order_service.py
# Остается как в предыдущем ответе, НО С ПОЛНЫМ CRUD
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ..utils import UUIDUtils

from ..repositories import OrderRepository, MaterialOnOrderRepository, ClientRepository, WorkerRepository
from ..models_sqlalchemy import Order as OrderSQL, MaterialOnOrder as MatOnOrderSQL
from ..models_pydantic import (
    MaterialOnOrderCreate, Order, OrderCreate, OrderUpdate, MaterialOnOrder, OrderStatus,
    Client, Worker, Material, MaterialOnOrderUpdate
)


from .client_service import ClientService
from .worker_service import WorkerService

from ...signal_bus import signalBus
from .material_service import MaterialService # Зависимость от другого сервиса

logger = logging.getLogger(__name__)

class OrderService:
    def __init__(self):
        self.order_repo = OrderRepository()
        self.mat_on_order_repo = MaterialOnOrderRepository()
        self.material_service = MaterialService() # Сервис материалов
        # Репозитории для проверки FK
        self.client_repo = ClientRepository()
        self.worker_repo = WorkerRepository()

    def get_order(self, db: Session, order_id: str, load_related: bool = False) -> Optional[Order]:
        logger.debug(f"Service: Getting order id {order_id}, load_related={load_related}")
        db_order = self.order_repo.get(db, id=order_id)
        if not db_order: return None

        # Базовое преобразование
        pydantic_order = Order.model_validate(db_order)

        # Опциональная загрузка связанных данных
        if load_related:
            try:
                # Используем существующие сервисы/репозитории для получения связанных Pydantic моделей
                if db_order.client_id:
                    client_service = ClientService()
                    pydantic_order.client = client_service.get_client(db, client_id=db_order.client_id)
                if db_order.worker_id:
                    worker_service = WorkerService()
                    pydantic_order.worker = worker_service.get_worker(db, worker_id=db_order.worker_id)

                # Загрузка материалов в заказе
                db_links = self.mat_on_order_repo.find_by_order_id(db, order_id=order_id)
                materials_in_order = []
                for db_link in db_links:
                    link_model = MaterialOnOrder.model_validate(db_link)
                    # Загружаем детали материала
                    link_model.material = self.material_service.get_material(db, material_id=db_link.material_id)
                    materials_in_order.append(link_model)
                pydantic_order.materials_on_order = materials_in_order
            except Exception as e:
                 logger.error(f"Service error loading related data for order {order_id}: {e}")
                 # Возвращаем заказ без связанных данных или с частичными данными

        return pydantic_order


    def get_orders(self, db: Session, skip: int = 0, limit: int = 100) -> List[Order]:
        logger.debug(f"Service: Getting multiple orders (skip={skip}, limit={limit})")
        db_orders = self.order_repo.get_multi(db, skip=skip, limit=limit)
        return [Order.model_validate(o) for o in db_orders] # Без связанных данных

    def get_orders_by_client(self, db: Session, client_id: str) -> List[Order]:
        logger.debug(f"Service: Getting orders for client {client_id}")
        db_orders = self.order_repo.find_by_client(db, client_id=client_id)
        return [Order.model_validate(o) for o in db_orders]

    def get_orders_by_worker(self, db: Session, worker_id: str) -> List[Order]:
        logger.debug(f"Service: Getting orders for worker {worker_id}")
        db_orders = self.order_repo.find_by_worker(db, worker_id=worker_id)
        return [Order.model_validate(o) for o in db_orders]

    def get_orders_by_status(self, db: Session, status: OrderStatus) -> List[Order]:
         logger.debug(f"Service: Getting orders with status {status.value}")
         db_orders = self.order_repo.find_by_status(db, status=status)
         return [Order.model_validate(o) for o in db_orders]


    def create_order_with_materials(self, db: Session, order_in: OrderCreate) -> Order:
        """ Создает заказ, связи с материалами и списывает баланс """
        logger.info(f"Service: Creating order for client {order_in.client_id}")

        materials_to_link = order_in.materials
        order_data = order_in.model_dump(exclude={'materials'})
        
        # Проверяем наличие даты и устанавливаем её, если не указана
        if 'date' not in order_data or not order_data['date']:
            order_data['date'] = datetime.now()

        # --- Проверки перед транзакцией ---
        if not self.client_repo.get(db, id=order_in.client_id):
             raise ValueError(f"Client with id {order_in.client_id} not found.")
        if order_in.worker_id and not self.worker_repo.get(db, id=order_in.worker_id):
             raise ValueError(f"Worker with id {order_in.worker_id} not found.")

        material_ids_amounts = {m.material_id: m.amount for m in materials_to_link}
        materials_to_update_balance = {} # Словарь {material_id: quantity_change}
        for mat_id, amount in material_ids_amounts.items():
            material = self.material_service.get_material(db, mat_id)
            if not material: raise ValueError(f"Material with id {mat_id} not found.")
            if material.balance < amount:
                 raise ValueError(f"Insufficient balance for material {material.type} ({material.id}). Need {amount}, have {material.balance}.")
            materials_to_update_balance[mat_id] = -amount # Отрицательное значение для списания

        # --- Транзакция ---
        try:
            # 1. Создаем основной заказ
            db_order = OrderSQL(**order_data)
            db_order.id = UUIDUtils.getUUID()
            db.add(db_order)
            db.flush() # Получаем ID заказа
            order_id = db_order.id
            logger.info(f"Order {order_id} flushed.")

            # 2. Создаем связи MaterialOnOrder
            created_links_db = []
            for link_data in materials_to_link:
                db_link = MatOnOrderSQL(
                    id=UUIDUtils.getUUID(),
                    order_id=order_id,
                    material_id=link_data.material_id,
                    amount=link_data.amount
                )
                db.add(db_link)
                created_links_db.append(db_link)
            db.flush() # Получаем ID связей, если нужно

            # 3. Списываем балансы материалов
            for mat_id, change in materials_to_update_balance.items():
                # Используем ВНУТРЕННИЙ вызов репозитория для обновления баланса В ТЕКУЩЕЙ ТРАНЗАКЦИИ
                # НЕ вызываем material_service.change_balance, т.к. он делает commit/rollback
                updated_mat = self.material_service.repository.update_balance(db, material_id=mat_id, change=change)
                if not updated_mat:
                     # Эта ошибка не должна возникать из-за предварительной проверки, но нужна защита от гонок
                     raise ValueError(f"Concurrency Error: Failed to update balance for material {mat_id} during order creation.")

            # 4. Фиксируем транзакцию
            db.commit()
            db.refresh(db_order)
            for link in created_links_db: db.refresh(link) # Обновляем и связи

            logger.info(f"Service: Successfully created order {order_id} with materials and updated balances.")

            # 5. Возвращаем результат и эмитируем сигнал
            pydantic_order = self.get_order(db, order_id, load_related=True) # Получаем с подгруженными данными
            if pydantic_order:
                 signalBus.order_created.emit(pydantic_order.model_dump())
                 return pydantic_order
            else: # Маловероятно, но возможно
                 raise Exception("Failed to reload created order.")

        except Exception as e:
            logger.error(f"Service Error creating order with materials: {e}")
            db.rollback()
            signalBus.database_error.emit(f"Ошибка создания заказа: {e}")
            raise


    def update_order(self, db: Session, order_id: str, order_in: OrderUpdate) -> Optional[Order]:
        """ Обновляет поля заказа (кроме материалов) """
        logger.info(f"Service: Updating order id {order_id}")
        db_order = self.order_repo.get(db, id=order_id)
        if not db_order: logger.warning(f"Order {order_id} not found"); return None

        update_data = order_in.model_dump(exclude_unset=True)

        # Проверка FK при их изменении
        if "client_id" in update_data and not self.client_repo.get(db, id=update_data["client_id"]):
             raise ValueError(f"Client with id {update_data['client_id']} not found.")
        if "worker_id" in update_data and update_data["worker_id"] and not self.worker_repo.get(db, id=update_data["worker_id"]):
             raise ValueError(f"Worker with id {update_data['worker_id']} not found.")

        if not update_data: return Order.model_validate(db_order) # Нет изменений

        try:
            original_status = db_order.status
            updated_db_order = self.order_repo.update(db, db_obj=db_order, obj_in=update_data)
            pydantic_order = Order.model_validate(updated_db_order)

            # Эмитируем сигналы
            signalBus.order_updated.emit(pydantic_order.model_dump())
            if "status" in update_data and updated_db_order.status != original_status:
                 signalBus.order_status_changed.emit(order_id, updated_db_order.status.value)

            # TODO: Добавить логику возврата материалов, если статус меняется на отмененный
            # if "status" in update_data and updated_db_order.status == OrderStatus.CANCELLED:
            #    self._return_materials_for_order(db, order_id)

            return pydantic_order
        except Exception as e:
             logger.error(f"Service Error updating order {order_id}: {e}")
             signalBus.database_error.emit(f"Ошибка обновления заказа: {e}")
             raise


    def delete_order(self, db: Session, order_id: str) -> bool:
        """ Удаляет заказ и связанные материалы (через cascade) """
        logger.info(f"Service: Deleting order id {order_id}")
        db_order = self.order_repo.get(db, id=order_id)
        if not db_order: logger.warning(f"Order {order_id} not found"); return False

        # TODO: Подумать о возврате материалов на склад при удалении заказа
        # Это зависит от бизнес-логики. Если заказ удаляется, значит ли это, что материалы не были использованы?
        # self._return_materials_for_order(db, order_id) # Вызвать перед удалением

        try:
            # Используем cascade="all, delete-orphan" в модели Order для materials_link
            # SQLAlchemy должен автоматически удалить связанные MaterialOnOrder
            deleted = self.order_repo.remove(db, id=order_id)
            if deleted:
                signalBus.order_deleted.emit(order_id)
                return True
            return False # remove вернул None
        except Exception as e:
            logger.error(f"Service Error deleting order {order_id}: {e}")
            db.rollback()
            signalBus.database_error.emit(f"Ошибка удаления заказа {order_id}: {e}")
            raise

    # --- Вспомогательные методы для управления материалами в заказе (Примеры) ---

    def add_material_to_order(self, db: Session, order_id: str, material_id: str, amount: int) -> Optional[MaterialOnOrder]:
        """ Добавляет материал к существующему заказу и списывает баланс """
        logger.info(f"Service: Adding {amount} of material {material_id} to order {order_id}")
        db_order = self.order_repo.get(db, id=order_id)
        if not db_order: raise ValueError(f"Order {order_id} not found.")
        # TODO: Проверить статус заказа (можно ли добавлять материалы?)

        material = self.material_service.get_material(db, material_id)
        if not material: raise ValueError(f"Material {material_id} not found.")
        if material.balance < amount: raise ValueError(f"Insufficient balance for {material.type}.")

        # Проверяем, нет ли уже этого материала в заказе
        existing_link = db.execute(
            select(MatOnOrderSQL).where(
                MatOnOrderSQL.order_id == order_id,
                MatOnOrderSQL.material_id == material_id
            )
        ).scalar_one_or_none()

        if existing_link:
             raise ValueError(f"Material {material_id} already exists in order {order_id}. Use update amount.")

        try:
            # Добавляем связь
            link_create_data = MaterialOnOrderCreate(order_id=order_id, material_id=material_id, amount=amount)
            db_link = self.mat_on_order_repo.create(db, obj_in=link_create_data) # Используем стандартный create

            # Списываем баланс (через сервис, т.к. это отдельная операция)
            updated_mat = self.material_service.change_balance(db, material_id=material_id, quantity_change=-amount)
            if not updated_mat:
                 # Если списание не удалось (не должно из-за проверок, но все же)
                 # Откатываем добавление связи (нужен rollback всей транзакции)
                 raise ValueError(f"Failed to decrease balance for material {material_id}.")

            # Здесь commit не нужен, т.к. create и change_balance уже сделали commit
            # Чтобы выполнить все в ОДНОЙ транзакции, нужно переделать change_balance
            # и create, чтобы они не делали commit, а вызывающий метод делал commit в конце.
            # Пока оставляем так для простоты.

            pydantic_link = MaterialOnOrder.model_validate(db_link)
            signalBus.material_linked_to_order.emit(pydantic_link.model_dump())
            return pydantic_link

        except Exception as e:
            logger.error(f"Service error adding material to order: {e}")
            # Rollback здесь не сработает правильно, т.к. commit уже был
            signalBus.database_error.emit(f"Ошибка добавления материала к заказу: {e}")
            raise

    def remove_material_from_order(self, db: Session, link_id: str) -> bool:
         """ Удаляет связь материал-заказ и возвращает материал на склад """
         logger.info(f"Service: Removing material link id {link_id} from order.")
         db_link = self.mat_on_order_repo.get(db, id=link_id)
         if not db_link: logger.warning(f"Material link {link_id} not found"); return False

         order_id = db_link.order_id
         material_id = db_link.material_id
         amount_to_return = db_link.amount

         # TODO: Проверить статус заказа

         try:
             # Возвращаем материал на склад
             updated_mat = self.material_service.change_balance(db, material_id=material_id, quantity_change=amount_to_return)
             if not updated_mat:
                  # Если не удалось вернуть (странно, но возможно)
                  raise ValueError(f"Failed to return balance for material {material_id}.")

             # Удаляем саму связь
             deleted = self.mat_on_order_repo.remove(db, id=link_id)
             if deleted:
                 signalBus.material_unlinked_from_order.emit(link_id)
                 return True
             else:
                  # Если удаление не удалось, нужно откатить возврат баланса (сложно без транзакции)
                  logger.error(f"Failed to delete link {link_id} after returning balance.")
                  # Попытка вернуть баланс обратно (может не сработать)
                  self.material_service.change_balance(db, material_id=material_id, quantity_change=-amount_to_return)
                  raise ValueError("Inconsistent state: Balance returned but link not deleted.")

         except Exception as e:
             logger.error(f"Service error removing material from order: {e}")
             # Попытка отката здесь тоже сложна
             signalBus.database_error.emit(f"Ошибка удаления материала из заказа: {e}")
             raise

    def update_material_amount_in_order(self, db: Session, link_id: str, new_amount: int) -> Optional[MaterialOnOrder]:
         """ Изменяет количество материала в заказе и корректирует баланс """
         if new_amount <= 0: raise ValueError("New amount must be positive.")
         logger.info(f"Service: Updating material link {link_id} to amount {new_amount}")

         db_link = self.mat_on_order_repo.get(db, id=link_id)
         if not db_link: logger.warning(f"Link {link_id} not found"); return None

         material_id = db_link.material_id
         current_amount = db_link.amount
         amount_change = new_amount - current_amount # > 0 если добавили, < 0 если убрали

         if amount_change == 0: return MaterialOnOrder.model_validate(db_link) # Нет изменений

         # TODO: Проверить статус заказа

         try:
             # Корректируем баланс на складе (change будет < 0 если добавили в заказ)
             updated_mat = self.material_service.change_balance(db, material_id=material_id, quantity_change=-amount_change)
             if not updated_mat:
                  raise ValueError(f"Failed to adjust balance for material {material_id}. Check stock.")

             # Обновляем количество в связи
             link_update_data = MaterialOnOrderUpdate(amount=new_amount)
             updated_link = self.mat_on_order_repo.update(db, db_obj=db_link, obj_in=link_update_data)

             pydantic_link = MaterialOnOrder.model_validate(updated_link)
             # Можно добавить отдельный сигнал об изменении кол-ва материала в заказе
             signalBus.material_linked_to_order.emit(pydantic_link.model_dump()) # Используем общий сигнал пока
             return pydantic_link

         except Exception as e:
             logger.error(f"Service error updating material amount in order: {e}")
             # Откат сложен без транзакции
             signalBus.database_error.emit(f"Ошибка изменения кол-ва материала в заказе: {e}")
             raise

    def get_filtered_orders(self, db: Session, worker_id: Optional[str] = None, 
                          status: Optional[str] = None, client_id: Optional[str] = None,
                          date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> List[Order]:
        """Get orders with various filters"""
        logger.debug(f"Service: Getting filtered orders worker={worker_id} status={status} client={client_id}")
        
        filters = {}
        if worker_id:
            filters['worker_id'] = worker_id
        if status:
            filters['status'] = status
        if client_id:
            filters['client_id'] = client_id
            
        # Date range is handled separately
        db_orders = self.order_repo.find_with_filters(db, filters, date_from, date_to)
        return [Order.model_validate(o) for o in db_orders]
        
    def count_orders_by_status(self, db: Session, status: str, worker_id: Optional[str] = None) -> int:
        """Count orders by status"""
        logger.debug(f"Service: Counting orders status={status} worker={worker_id}")
        
        filters = {'status': status}
        if worker_id:
            filters['worker_id'] = worker_id
            
        return self.order_repo.count_with_filters(db, filters)

# Аналогично создаем services/material_on_order_service.py и services/material_provider_service.py
# с полными CRUD методами, если нужна отдельная логика для них.