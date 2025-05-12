# controllers.py
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import logging

# Импортируем сервисы, Pydantic модели, get_db
from .services.client_service import ClientService
from .services.worker_service import WorkerService
from .services.provider_service import ProviderService
from .services.material_service import MaterialService
from .services.order_service import OrderService
from .services.auth_service import AuthService # Новый сервис аутентификации
from .services.material_provider_service import MaterialProviderService # Сервис для связей

from ..signal_bus import signalbus

from .models_pydantic import (
    Client, ClientCreate, ClientUpdate, Order, OrderCreate, OrderUpdate,
    Worker, WorkerCreate, WorkerUpdate, Provider, ProviderCreate, ProviderUpdate,
    Material, MaterialCreate, MaterialUpdate, MaterialOnOrder, MaterialProvider, MaterialProviderCreate,
    OrderStatus, LoginRequest, AuthenticatedUser, BaseModel as PydanticBaseModel
)
from .database import get_db # Важно для получения сессии

logger = logging.getLogger(__name__)
# SignalBus используется в сервисах

# --- Базовый контроллер ( stateless ) ---
class BaseController: pass

# --- Контроллеры CRUD ---

class ClientController(BaseController):
    def __init__(self): self.service = ClientService()
    def get_one(self, db: Session, id: str) -> Optional[Client]:
        logger.debug(f"Ctrl: Get client id={id}")
        return self.service.get_client(db, client_id=id)
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Client]:
        logger.debug(f"Ctrl: Get clients skip={skip} limit={limit}")
        return self.service.get_clients(db, skip=skip, limit=limit)
    def create(self, db: Session, data: ClientCreate) -> Optional[Client]:
        logger.debug(f"Ctrl: Create client username={data.username}")
        try: return self.service.create_client(db, client_in=data)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return None
    def update(self, db: Session, id: str, data: ClientUpdate) -> Optional[Client]:
        logger.debug(f"Ctrl: Update client id={id}")
        try: return self.service.update_client(db, client_id=id, client_in=data)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return None
    def delete(self, db: Session, id: str) -> bool:
        logger.debug(f"Ctrl: Delete client id={id}")
        try: return self.service.delete_client(db, client_id=id)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return False

class WorkerController(BaseController):
    def __init__(self): self.service = WorkerService()
    def get_one(self, db: Session, id: str) -> Optional[Worker]:
        logger.debug(f"Ctrl: Get worker id={id}")
        return self.service.get_worker(db, worker_id=id)
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Worker]:
        logger.debug(f"Ctrl: Get workers skip={skip} limit={limit}")
        return self.service.get_workers(db, skip=skip, limit=limit)
    def create(self, db: Session, data: WorkerCreate) -> Optional[Worker]:
        logger.debug(f"Ctrl: Create worker username={data.username}")
        try: return self.service.create_worker(db, worker_in=data)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return None
    def update(self, db: Session, id: str, data: WorkerUpdate) -> Optional[Worker]:
        logger.debug(f"Ctrl: Update worker id={id}")
        try: return self.service.update_worker(db, worker_id=id, worker_in=data)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return None
    def delete(self, db: Session, id: str) -> bool:
        logger.debug(f"Ctrl: Delete worker id={id}")
        try: return self.service.delete_worker(db, worker_id=id)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return False

class ProviderController(BaseController):
    def __init__(self): self.service = ProviderService()
    def get_one(self, db: Session, id: str) -> Optional[Provider]:
        logger.debug(f"Ctrl: Get provider id={id}")
        return self.service.get_provider(db, provider_id=id)
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Provider]:
        logger.debug(f"Ctrl: Get providers skip={skip} limit={limit}")
        return self.service.get_providers(db, skip=skip, limit=limit)
    def create(self, db: Session, data: ProviderCreate) -> Optional[Provider]:
        logger.debug(f"Ctrl: Create provider name={data.name}")
        try: return self.service.create_provider(db, provider_in=data)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return None
    def update(self, db: Session, id: str, data: ProviderUpdate) -> Optional[Provider]:
        logger.debug(f"Ctrl: Update provider id={id}")
        try: return self.service.update_provider(db, provider_id=id, provider_in=data)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return None
    def delete(self, db: Session, id: str) -> bool:
        logger.debug(f"Ctrl: Delete provider id={id}")
        try: return self.service.delete_provider(db, provider_id=id)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return False

class MaterialController(BaseController):
    def __init__(self): self.service = MaterialService()
    def get_one(self, db: Session, id: str) -> Optional[Material]:
        logger.debug(f"Ctrl: Get material id={id}")
        return self.service.get_material(db, material_id=id)
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Material]:
        logger.debug(f"Ctrl: Get materials skip={skip} limit={limit}")
        return self.service.get_materials(db, skip=skip, limit=limit)
    def create(self, db: Session, data: MaterialCreate) -> Optional[Material]:
        logger.debug(f"Ctrl: Create material type={data.type}")
        try: return self.service.create_material(db, material_in=data)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return None
    def update(self, db: Session, id: str, data: MaterialUpdate) -> Optional[Material]:
        logger.debug(f"Ctrl: Update material id={id}")
        try: return self.service.update_material(db, material_id=id, material_in=data)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return None
    def delete(self, db: Session, id: str) -> bool:
        logger.debug(f"Ctrl: Delete material id={id}")
        try: return self.service.delete_material(db, material_id=id)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return False
    def adjust_balance(self, db: Session, material_id: str, quantity_change: int) -> Optional[Material]:
        logger.debug(f"Ctrl: Adjust balance material={material_id} change={quantity_change}")
        try: return self.service.change_balance(db, material_id=material_id, quantity_change=quantity_change)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return None

class OrderController(BaseController):
    def __init__(self): self.service = OrderService()
    def get_one(self, db: Session, id: str, load_related: bool = True) -> Optional[Order]:
        logger.debug(f"Ctrl: Get order id={id} related={load_related}")
        return self.service.get_order(db, order_id=id, load_related=load_related)
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Order]:
        logger.debug(f"Ctrl: Get orders skip={skip} limit={limit}")
        return self.service.get_orders(db, skip=skip, limit=limit)
    def get_by_client(self, db: Session, client_id: str) -> List[Order]:
         logger.debug(f"Ctrl: Get orders client={client_id}")
         return self.service.get_orders_by_client(db, client_id=client_id)
    def get_by_worker(self, db: Session, worker_id: str) -> List[Order]:
         logger.debug(f"Ctrl: Get orders worker={worker_id}")
         return self.service.get_orders_by_worker(db, worker_id=worker_id)
    def get_by_status(self, db: Session, status: OrderStatus) -> List[Order]:
          logger.debug(f"Ctrl: Get orders status={status.value}")
          return self.service.get_orders_by_status(db, status=status)
    def create_with_materials(self, db: Session, data: OrderCreate) -> Optional[Order]:
        logger.debug(f"Ctrl: Create order client={data.client_id}")
        try: return self.service.create_order_with_materials(db, order_in=data)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return None
    def update(self, db: Session, id: str, data: OrderUpdate) -> Optional[Order]:
        # Этот метод обновляет только поля самого заказа, не материалы
        logger.debug(f"Ctrl: Update order id={id}")
        try: return self.service.update_order(db, order_id=id, order_in=data)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return None
    def delete(self, db: Session, id: str) -> bool:
        logger.debug(f"Ctrl: Delete order id={id}")
        try: return self.service.delete_order(db, order_id=id)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return False
    # Методы для управления материалами в заказе
    def add_material(self, db: Session, order_id: str, material_id: str, amount: int) -> Optional[MaterialOnOrder]:
         logger.debug(f"Ctrl: Add material={material_id} amount={amount} to order={order_id}")
         try: return self.service.add_material_to_order(db, order_id=order_id, material_id=material_id, amount=amount)
         except Exception as e: logger.error(f"Ctrl Error: {e}"); return None
    def remove_material(self, db: Session, link_id: str) -> bool:
         logger.debug(f"Ctrl: Remove material link_id={link_id}")
         try: return self.service.remove_material_from_order(db, link_id=link_id)
         except Exception as e: logger.error(f"Ctrl Error: {e}"); return False
    def update_material_amount(self, db: Session, link_id: str, new_amount: int) -> Optional[MaterialOnOrder]:
        logger.debug(f"Ctrl: Update material link_id={link_id} amount={new_amount}")
        try: return self.service.update_material_amount_in_order(db, link_id=link_id, new_amount=new_amount)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return None


class MaterialProviderController(BaseController):
     def __init__(self): self.service = MaterialProviderService()
     def link(self, db: Session, data: MaterialProviderCreate) -> Optional[MaterialProvider]:
         logger.debug(f"Ctrl: Link provider={data.provider_id} material={data.material_id}")
         try: return self.service.link_material_to_provider(db, link_in=data)
         except Exception as e: logger.error(f"Ctrl Error: {e}"); return None
     def unlink(self, db: Session, link_id: Optional[str] = None, *, provider_id: Optional[str] = None, material_id: Optional[str] = None) -> bool:
         logger.debug(f"Ctrl: Unlink link_id={link_id} provider={provider_id} material={material_id}")
         try: return self.service.unlink_material_from_provider(db, link_id=link_id, provider_id=provider_id, material_id=material_id)
         except Exception as e: logger.error(f"Ctrl Error: {e}"); return False
     def get_by_provider(self, db: Session, provider_id: str) -> List[MaterialProvider]:
         logger.debug(f"Ctrl: Get links for provider={provider_id}")
         return self.service.get_links_by_provider(db, provider_id=provider_id)
     def get_by_material(self, db: Session, material_id: str) -> List[MaterialProvider]:
         logger.debug(f"Ctrl: Get links for material={material_id}")
         return self.service.get_links_by_material(db, material_id=material_id)


# --- Контроллер аутентификации ---
class AuthController(BaseController):
    def __init__(self):
        self.service = AuthService()

    def login(self, db: Session, login_data: LoginRequest) -> Optional[AuthenticatedUser]:
        """ Обрабатывает запрос на вход """
        logger.info(f"Controller: Handling login attempt for user {login_data.username}")
        # Сервис сам отправит сигналы success/failure
        return self.service.authenticate(db, username=login_data.username, password=login_data.password)

    # Регистрация теперь раздельная для клиентов и работников
    # Используем соответствующие контроллеры (ClientController, WorkerController)

    def logout(self):
        """ Обрабатывает выход пользователя """
        # На стороне бэкенда обычно ничего делать не нужно, если нет сессий/токенов
        logger.info("Controller: Handling logout")
        signalbus.logout_completed.emit()