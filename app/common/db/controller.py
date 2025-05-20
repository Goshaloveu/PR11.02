# controllers.py
from typing import Dict, List, Any, Optional, Type, TypeVar, Generic
from sqlalchemy.orm import Session
import logging
import re
from datetime import datetime
from sqlalchemy import and_, or_, not_
import uuid

# Импортируем модели базы данных
from . import models_sqlalchemy as models
from . import models_pydantic as pd_models
from .models_pydantic import LoginRequest, ClientUpdate, ClientCreate, WorkerUpdate, WorkerCreate

# Импортируем сервисы
from .services import client_service, worker_service, provider_service, material_service, order_service, auth_service
from .services.auth_service import AuthService
from .services.material_provider_service import MaterialProviderService

# Импортируем шину сигналов
from ..signal_bus import signalBus

from .models_pydantic import (
    Client, ClientCreate, ClientUpdate, Order, OrderCreate, OrderUpdate,
    Worker, WorkerCreate, WorkerUpdate, Provider, ProviderCreate, ProviderUpdate,
    Material, MaterialCreate, MaterialUpdate, MaterialOnOrder, MaterialProvider, MaterialProviderCreate,
    OrderStatus, AuthenticatedUser, BaseModel as PydanticBaseModel
)
from .database import get_db # Важно для получения сессии
from .utils import get_password_hash, verify_password, extract_phone_digits

logger = logging.getLogger(__name__)
# SignalBus используется в сервисах

# --- Базовый контроллер ( stateless ) ---
class BaseController:
    def __init__(self):
        pass

# --- Контроллеры CRUD ---

class ClientController(BaseController):
    def __init__(self):
        super().__init__()
        self.service = client_service.ClientService()
    def get_one(self, db: Session, id: str) -> Optional[Client]:
        logger.debug(f"Ctrl: Get client id={id}")
        return self.service.get_client(db, client_id=id)
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Client]:
        logger.debug(f"Ctrl: Get clients skip={skip} limit={limit}")
        return self.service.get_clients(db, skip=skip, limit=limit)
    def create(self, db: Session, client_create: ClientCreate) -> Optional[Client]:
        try:
            # Extract phone digits for consistent storage
            phone_digits = extract_phone_digits(client_create.phone)
            
            # Check if client with this phone already exists
            existing_client = self.get_by_phone(db, phone_digits)
            if existing_client:
                raise ValueError(f"Client with phone {client_create.phone} already exists")
            
            # Create client data dictionary from pydantic model
            client_data = client_create.model_dump()
            
            # Set current date and ensure ID is set
            client_data["date"] = datetime.now()
            client_data["id"] = str(uuid.uuid4())
            
            # Extract password before creating the client instance
            password = client_data.pop("password")
            hash_password = password
            
            # Create client model instance with hash_password
            db_client = models.Client(**client_data, hash_password=hash_password)
            
            # Add to database
            db.add(db_client)
            db.commit()
            db.refresh(db_client)
            
            return db_client
        except Exception as e:
            db.rollback()
            print(f"Service Error creating client: {str(e)}")
            raise
    def update(self, db: Session, id: str, data: ClientUpdate) -> Optional[Client]:
        logger.debug(f"Ctrl: Update client id={id}")
        try: return self.service.update_client(db, client_id=id, client_in=data)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return None
    def delete(self, db: Session, id: str) -> bool:
        logger.debug(f"Ctrl: Delete client id={id}")
        try: return self.service.delete_client(db, client_id=id)
        except Exception as e: logger.error(f"Ctrl Error: {e}"); return False
    def get_by_phone(self, db: Session, phone: str) -> Optional[Client]:
        logger.debug(f"Ctrl: Get client by phone={phone}")
        try: 
            # Find by phone - directly return the service result without wrapping or mapping
            return self.service.get_client_by_phone(db, phone=phone)
        except Exception as e: 
            logger.error(f"Ctrl Error: {e}")
            return None
    def get_by_email_or_phone(self, db: Session, email: str, phone: str) -> Optional[Client]:
        logger.debug(f"Ctrl: Get client by email={email} or phone={phone}")
        try:
            # First try by phone
            client = self.get_by_phone(db, phone)
            if client:
                return client
            # Then try by email
            clients = self.get_all(db)
            for client in clients:
                if client.mail == email:
                    return client
            return None
        except Exception as e:
            logger.error(f"Ctrl Error: {e}")
            return None

class WorkerController(BaseController):
    def __init__(self): self.service = worker_service.WorkerService()
    def get_one(self, db: Session, id: str) -> Optional[Worker]:
        logger.debug(f"Ctrl: Get worker id={id}")
        return self.service.get_worker(db, worker_id=id)
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Worker]:
        logger.debug(f"Ctrl: Get workers skip={skip} limit={limit}")
        return self.service.get_workers(db, skip=skip, limit=limit)
    def create(self, db: Session, data: WorkerCreate) -> Optional[Worker]:
        logger.debug(f"Ctrl: Create worker with phone={data.phone}")
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
    def get_by_phone(self, db: Session, phone: str) -> Optional[Worker]:
        logger.debug(f"Ctrl: Get worker by phone={phone}")
        try: 
            # Find by phone
            return self.service.get_worker_by_phone(db, phone=phone)
        except Exception as e: 
            logger.error(f"Ctrl Error: {e}")
            return None

class ProviderController(BaseController):
    def __init__(self): self.service = provider_service.ProviderService()
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
    def __init__(self): self.service = material_service.MaterialService()
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
    def __init__(self): self.service = order_service.OrderService()
    def get_one(self, db: Session, id: str, load_related: bool = True) -> Optional[Order]:
        logger.debug(f"Ctrl: Get order id={id} related={load_related}")
        return self.service.get_order(db, order_id=id, load_related=load_related)
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Order]:
        logger.debug(f"Ctrl: Get orders skip={skip} limit={limit}")
        return self.service.get_orders(db, skip=skip, limit=limit)
    def get_by_client(self, db: Session, client_id: str, status: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Order]:
         logger.debug(f"Ctrl: Get orders client={client_id}")
         return self.service.get_orders_by_client(db, client_id=client_id)
    def get_orders_by_client(self, client_id: str) -> List[Order]:
        """Получает все заказы для клиента по его ID"""
        logger.debug(f"Ctrl: Get orders for client={client_id}")
        from .database import SessionLocal
        db = SessionLocal()
        try:
            return self.service.get_orders_by_client(db, client_id=client_id)
        finally:
            db.close()
    def get_by_worker(self, db: Session, worker_id: str) -> List[Order]:
         logger.debug(f"Ctrl: Get orders worker={worker_id}")
         return self.service.get_orders_by_worker(db, worker_id=worker_id)
    def get_by_status(self, db: Session, status: OrderStatus) -> List[Order]:
          logger.debug(f"Ctrl: Get orders status={status.value}")
          return self.service.get_orders_by_status(db, status=status)
    def create(self, db: Session, data: OrderCreate) -> Optional[Order]:
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
    def get_by_id(self, db: Session, order_id: str) -> Optional[Order]:
        logger.debug(f"Ctrl: Get order by id={order_id}")
        return self.get_one(db, order_id, load_related=True)
    
    def get_filtered_orders(self, db: Session, worker_id: Optional[str] = None, 
                           status: Optional[str] = None, client_id: Optional[str] = None,
                           date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> List[Order]:
        """Get orders with filters"""
        logger.debug(f"Ctrl: Get filtered orders worker={worker_id} status={status} client={client_id}")
        try: 
            return self.service.get_filtered_orders(
                db, worker_id=worker_id, status=status, 
                client_id=client_id, date_from=date_from, date_to=date_to
            )
        except Exception as e: 
            logger.error(f"Ctrl Error: {e}")
            return []
            
    def count_by_status(self, db: Session, status: str, worker_id: Optional[str] = None) -> int:
        """Count orders by status"""
        logger.debug(f"Ctrl: Count orders status={status} worker={worker_id}")
        try: 
            return self.service.count_orders_by_status(db, status=status, worker_id=worker_id)
        except Exception as e: 
            logger.error(f"Ctrl Error: {e}")
            return 0

class MaterialProviderController(BaseController):
     def __init__(self): self.service = MaterialProviderService()
     def link(self, db: Session, data: MaterialProviderCreate) -> Optional[MaterialProvider]:
         logger.debug(f"Ctrl: Link provider={data.provider_id} with material={data.material_id}")
         try: return self.service.link_provider_material(db, link_data=data)
         except Exception as e: logger.error(f"Ctrl Error: {e}"); return None
     def unlink(self, db: Session, link_id: Optional[str] = None, *, provider_id: Optional[str] = None, material_id: Optional[str] = None) -> bool:
         logger.debug(f"Ctrl: Unlink link_id={link_id} or provider={provider_id} material={material_id}")
         try: return self.service.unlink_provider_material(db, link_id=link_id, provider_id=provider_id, material_id=material_id)
         except Exception as e: logger.error(f"Ctrl Error: {e}"); return False
     def get_by_provider(self, db: Session, provider_id: str) -> List[MaterialProvider]:
         logger.debug(f"Ctrl: Get MaterialProvider by provider={provider_id}")
         return self.service.get_links_by_provider(db, provider_id=provider_id)
     def get_by_material(self, db: Session, material_id: str) -> List[MaterialProvider]:
         logger.debug(f"Ctrl: Get MaterialProvider by material={material_id}")
         return self.service.get_links_by_material(db, material_id=material_id)

class AuthController(BaseController):
    def __init__(self):
        self.service = auth_service.AuthService()
        
    def extract_phone_digits(self, phone: str) -> str:
        """Извлекает 10 цифр номера телефона из разных форматов"""
        # Очищаем от всех символов кроме цифр
        phone_digits = re.sub(r'[^0-9]', '', phone)
        # Берем последние 10 цифр (без кода страны)
        if len(phone_digits) >= 10:
            return phone_digits[-10:]
        return phone_digits
        
    def login(self, db: Session, login_data: LoginRequest) -> dict:
        """Authenticates user by phone and password and returns user data."""
        # Используем выделенный метод для извлечения цифр телефона
        phone_digits = self.extract_phone_digits(login_data.phone)
        
        logger.debug(f"Login attempt with original phone: {login_data.phone}, extracted digits: {phone_digits}")
        
        user_type = login_data.user_type if hasattr(login_data, 'user_type') else "client"
        logger.debug(f"Login type: {user_type}")
        
        # Try to authenticate as client first
        if user_type == "client":
            logger.debug(f"Trying to authenticate as client with phone_digits: {phone_digits}")
            client = self._get_client_by_phone(db, phone_digits)
            if client:
                # Debug logs to see what we're working with
                logger.debug(f"Found client with phone {phone_digits}, checking attributes...")
                logger.debug(f"Client attributes: {dir(client)}")
                logger.debug(f"Client has hash_password: {'hash_password' in dir(client)}")
                logger.debug(f"Client phone in DB: {client.phone}")
                
                if self.verify_password(db, phone_digits, login_data.password, is_employee=False):
                    client_dict = {}
                    # Create a dictionary from the SQLAlchemy object instead of using vars()
                    for column in client.__table__.columns:
                        if column.name != 'hash_password':  # Exclude password hash
                            client_dict[column.name] = getattr(client, column.name)
                    
                    # Signal successful login for client
                    logger.debug(f"Client login successful: {client_dict['first']} {client_dict['last']}")
                    signalBus.login_successful.emit("client", client_dict)
                    return client_dict
                else:
                    logger.debug(f"Client password verification failed for phone: {phone_digits}")
                    signalBus.login_failed.emit("Неверный пароль")
                    raise ValueError("Неверный пароль")
            else:
                logger.debug(f"Client not found with phone: {phone_digits}")
                signalBus.login_failed.emit(f"Клиент с номером телефона {login_data.phone} не найден")
                raise ValueError(f"Клиент с номером телефона {login_data.phone} не найден")
        
        # Try to authenticate as worker if client authentication failed or user_type is worker
        elif user_type == "worker":
            logger.debug(f"Trying to authenticate as worker with phone_digits: {phone_digits}")
            worker = self._get_worker_by_phone(db, phone_digits)
            if worker:
                # Debug logs for worker as well
                logger.debug(f"Found worker with phone {phone_digits}, checking attributes...")
                logger.debug(f"Worker attributes: {dir(worker)}")
                logger.debug(f"Worker has hash_password: {'hash_password' in dir(worker)}")
                logger.debug(f"Worker phone in DB: {worker.phone}")
                
                if self.verify_password(db, phone_digits, login_data.password, is_employee=True):
                    worker_dict = {}
                    # Create a dictionary from the SQLAlchemy object
                    for column in worker.__table__.columns:
                        if column.name != 'hash_password':  # Exclude password hash
                            worker_dict[column.name] = getattr(worker, column.name)
                    
                    # Signal successful login for worker
                    logger.debug(f"Worker login successful: {worker_dict['first']} {worker_dict['last']}")
                    signalBus.login_successful.emit("worker", worker_dict)
                    return worker_dict
                else:
                    logger.debug(f"Worker password verification failed for phone: {phone_digits}")
                    signalBus.login_failed.emit("Неверный пароль")
                    raise ValueError("Неверный пароль")
            else:
                logger.debug(f"Worker not found with phone: {phone_digits}")
                signalBus.login_failed.emit(f"Сотрудник с номером телефона {login_data.phone} не найден")
                raise ValueError(f"Сотрудник с номером телефона {login_data.phone} не найден")
                
        # If we get here, authentication failed
        signalBus.login_failed.emit("Ошибка аутентификации")
        raise ValueError("Ошибка аутентификации")
    
    def logout(self):
        """Logs out the current user."""
        # Signal logout
        signalBus.logout_completed.emit()
        
    def verify_password(self, db: Session, phone: str, password: str, is_employee: bool = False) -> bool:
        """
        Проверяет пароль пользователя
        """
        logger.debug(f"Auth controller: Verifying password for {'worker' if is_employee else 'client'} with phone '{phone}'")
        
        # Извлекаем 10 цифр телефона
        phone_digits = self.extract_phone_digits(phone)
        
        if is_employee:
            user = self._get_worker_by_phone(db, phone_digits)
        else:
            user = self._get_client_by_phone(db, phone_digits)
            
        if not user:
            logger.warning(f"User with phone '{phone}' not found for password verification")
            return False
            
        return self.service.password_service.verify_password(password, user.hash_password)
    
    def _get_client_by_phone(self, db: Session, phone: str):
        """
        Получает клиента по номеру телефона
        """
        client_controller = ClientController()
        client = client_controller.get_by_phone(db, phone)
        logger.debug(f"Retrieved raw client object for phone {phone}: {client}")
        if client:
            logger.debug(f"Client type: {type(client)}")
            # Debug: show the client's phone number in DB to help troubleshoot
            logger.debug(f"Client phone in DB: {client.phone}, comparing with requested: {phone}")
        else:
            # Try different formats if client not found
            logger.debug(f"Client not found with exact phone match: {phone}, trying alternative formats")
            # If we're looking for a 10-digit number, also try with +7 prefix
            if len(phone) == 10:
                alt_phone = phone  # Try the original 10-digit format
                client = client_controller.get_by_phone(db, alt_phone)
                if not client and phone.isdigit():
                    # Try with +7 prefix
                    alt_phone = "+7" + phone
                    logger.debug(f"Trying with +7 prefix: {alt_phone}")
                    client = client_controller.get_by_phone(db, alt_phone)
            
            # If we're looking for a phone with +7 prefix, also try just the 10 digits
            elif phone.startswith("+7") and len(phone) > 2:
                alt_phone = phone[2:]  # Remove +7 prefix
                logger.debug(f"Trying without +7 prefix: {alt_phone}")
                client = client_controller.get_by_phone(db, alt_phone)
                
            if client:
                logger.debug(f"Found client with alternative phone format: {client.phone}")
        
        return client
        
    def _get_worker_by_phone(self, db: Session, phone: str):
        """
        Получает работника по номеру телефона
        """
        worker_controller = WorkerController()
        worker = worker_controller.get_by_phone(db, phone)
        logger.debug(f"Retrieved raw worker object for phone {phone}: {worker}")
        if worker:
            logger.debug(f"Worker type: {type(worker)}")
            # Debug: show the worker's phone number in DB to help troubleshoot
            logger.debug(f"Worker phone in DB: {worker.phone}, comparing with requested: {phone}")
        else:
            # Try different formats if worker not found
            logger.debug(f"Worker not found with exact phone match: {phone}, trying alternative formats")
            # If we're looking for a 10-digit number, also try with +7 prefix
            if len(phone) == 10:
                alt_phone = phone  # Try the original 10-digit format
                worker = worker_controller.get_by_phone(db, alt_phone)
                if not worker and phone.isdigit():
                    # Try with +7 prefix
                    alt_phone = "+7" + phone
                    logger.debug(f"Trying with +7 prefix: {alt_phone}")
                    worker = worker_controller.get_by_phone(db, alt_phone)
            
            # If we're looking for a phone with +7 prefix, also try just the 10 digits
            elif phone.startswith("+7") and len(phone) > 2:
                alt_phone = phone[2:]  # Remove +7 prefix
                logger.debug(f"Trying without +7 prefix: {alt_phone}")
                worker = worker_controller.get_by_phone(db, alt_phone)
                
            if worker:
                logger.debug(f"Found worker with alternative phone format: {worker.phone}")
                
        return worker

T = TypeVar('T')