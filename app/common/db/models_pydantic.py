# models_pydantic.py
import re
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, EmailStr
from enum import Enum
from .utils import UUIDUtils # Импортируем твой класс

# --- Константы и валидаторы --- (Оставляем как есть)
NAME_REGEX = r'^[а-яА-Яёa-zA-Z-]+$'
PHONE_REGEX = r'^(\+7[0-9]{10}|8[0-9]{10})$'
INN_REGEX = r'^[0-9]{10,12}$'
PASS_SERIES_REGEX = r'^[0-9]{4}$'
PASS_NUMBER_REGEX = r'^[0-9]{6}$'

def validate_regex(value: Optional[str], pattern: str, field_name: str) -> Optional[str]:
    if value is None: return value
    if not re.match(pattern, value):
        raise ValueError(f'{field_name} format is invalid ("{value}")')
    return value

# --- Enum ---
class OrderStatus(str, Enum):
    PROCESSING = 'Обработка'
    IN_PROGRESS = 'В работе'
    COMPLETED = 'Выполнен'

# --- Базовая модель ---
class BaseEntity(BaseModel):
     id: str = Field(default_factory=UUIDUtils.getUUID, alias='id_')
     class Config:
        orm_mode = True
        populate_by_name = True

# --- Модели данных ---

# --- Client ---
class ClientBase(BaseModel):
    # Основные поля
    first: str = Field(..., min_length=1, max_length=100)
    last: str = Field(..., min_length=1, max_length=100)
    middle: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=12)
    mail: Optional[EmailStr] = Field(None, max_length=200)
    # Поля для аутентификации

    # Валидаторы
    @field_validator('first', 'last')
    def validate_names(cls, v): return validate_regex(v, NAME_REGEX, 'Name')
    @field_validator('middle')
    def validate_middle_name(cls, v): return validate_regex(v, NAME_REGEX, 'Middle Name') if v else v
    @field_validator('phone')
    def validate_phone_format(cls, v): return validate_regex(v, PHONE_REGEX, 'Phone') if v else v
    @field_validator('username')
    def validate_username(cls, v):
        # Простая проверка, можно усложнить (только буквы/цифры и т.д.)
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError('Username can only contain letters, numbers, and . - _')
        return v

class ClientCreate(ClientBase):
    password: str = Field(..., min_length=6) # Пароль обязателен при создании

class ClientUpdate(BaseModel): # Отдельная модель для обновления
    first: Optional[str] = Field(None, min_length=1, max_length=100)
    last: Optional[str] = Field(None, min_length=1, max_length=100)
    middle: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=12)
    mail: Optional[EmailStr] = Field(None, max_length=200)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    password: Optional[str] = Field(None, min_length=6) # Для смены пароля

    # Валидаторы применяются, если поле передано
    @field_validator('first', 'last', mode='before')
    def check_names_update(cls, v): return validate_regex(v, NAME_REGEX, 'Name') if v else v
    @field_validator('middle', mode='before')
    def check_middle_update(cls, v): return validate_regex(v, NAME_REGEX, 'Middle Name') if v else v
    @field_validator('phone', mode='before')
    def check_phone_update(cls, v): return validate_regex(v, PHONE_REGEX, 'Phone') if v else v
    @field_validator('username', mode='before')
    def check_username_update(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9_.-]+$', v):
             raise ValueError('Username can only contain letters, numbers, and . - _')
        return v

class Client(ClientBase, BaseEntity): # Модель для чтения из БД
    date: datetime
    # НЕ СОДЕРЖИТ HASHED_PASSWORD для безопасности

# --- Worker ---
class WorkerBase(BaseModel):
    first: str = Field(..., min_length=1, max_length=100)
    last: Optional[str] = Field(None, max_length=100)
    middle: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=12)
    mail: Optional[EmailStr] = Field(None, max_length=200)
    pass_series: Optional[str] = Field(None, max_length=4)
    pass_number: Optional[str] = Field(None, max_length=6)
    position: str = Field(..., min_length=1, max_length=200)
    born_date: Optional[datetime] = None
    # Поля для аутентификации

    # Валидаторы
    @field_validator('first')
    def validate_worker_first_name(cls, v): return validate_regex(v, NAME_REGEX, 'First Name')
    @field_validator('last', 'middle')
    def validate_worker_optional_names(cls, v): return validate_regex(v, NAME_REGEX, 'Name part') if v else v
    @field_validator('phone')
    def validate_worker_phone(cls, v): return validate_regex(v, PHONE_REGEX, 'Phone') if v else v
    @field_validator('pass_series')
    def validate_pass_series(cls, v): return validate_regex(v, PASS_SERIES_REGEX, 'Passport Series') if v else v
    @field_validator('pass_number')
    def validate_pass_number(cls, v): return validate_regex(v, PASS_NUMBER_REGEX, 'Passport Number') if v else v
    @field_validator('username')
    def validate_worker_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError('Username can only contain letters, numbers, and . - _')
        return v

class WorkerCreate(WorkerBase):
    password: str = Field(..., min_length=6)

class WorkerUpdate(BaseModel): # Отдельная модель
    first: Optional[str] = Field(None, min_length=1, max_length=100)
    last: Optional[str] = Field(None, max_length=100)
    middle: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=12)
    mail: Optional[EmailStr] = Field(None, max_length=200)
    pass_series: Optional[str] = Field(None, max_length=4)
    pass_number: Optional[str] = Field(None, max_length=6)
    position: Optional[str] = Field(None, min_length=1, max_length=200)
    born_date: Optional[datetime] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    password: Optional[str] = Field(None, min_length=6) # Для смены пароля

    # Валидаторы для необязательных полей (применяются, если значение передано)
    @field_validator('first', 'last', 'middle', mode='before')
    def check_worker_names_update(cls, v): return validate_regex(v, NAME_REGEX, 'Name part') if v else v
    @field_validator('phone', mode='before')
    def check_worker_phone_update(cls, v): return validate_regex(v, PHONE_REGEX, 'Phone') if v else v
    @field_validator('pass_series', mode='before')
    def check_pass_series_update(cls, v): return validate_regex(v, PASS_SERIES_REGEX, 'Passport Series') if v else v
    @field_validator('pass_number', mode='before')
    def check_pass_number_update(cls, v): return validate_regex(v, PASS_NUMBER_REGEX, 'Passport Number') if v else v
    @field_validator('username', mode='before')
    def check_worker_username_update(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9_.-]+$', v):
             raise ValueError('Username can only contain letters, numbers, and . - _')
        return v


class Worker(WorkerBase, BaseEntity):
    date: datetime
    # НЕ СОДЕРЖИТ HASHED_PASSWORD

# --- Provider, Material, Order, MaterialOnOrder, MaterialProvider ---
# --- Оставляем как в предыдущей версии (с Base, Create, Update, Read моделями) ---
# ... (Просто скопируйте их из предыдущего ответа, они не меняются) ...
# --- Provider ---
class ProviderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    inn: str = Field(..., max_length=12)
    phone: Optional[str] = Field(None, max_length=12)
    mail: Optional[EmailStr] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=200)
    @field_validator('inn')
    def validate_inn_format(cls, v): return validate_regex(v, INN_REGEX, 'INN')
    @field_validator('phone')
    def validate_provider_phone(cls, v): return validate_regex(v, PHONE_REGEX, 'Phone') if v else v
class ProviderCreate(ProviderBase): pass
class ProviderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    inn: Optional[str] = Field(None, max_length=12)
    phone: Optional[str] = Field(None, max_length=12)
    mail: Optional[EmailStr] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=200)
    # Валидаторы
    @field_validator('inn', mode='before')
    def check_inn_update(cls, v): return validate_regex(v, INN_REGEX, 'INN') if v else v
    @field_validator('phone', mode='before')
    def check_provider_phone_update(cls, v): return validate_regex(v, PHONE_REGEX, 'Phone') if v else v
class Provider(ProviderBase, BaseEntity): pass

# --- Material ---
class MaterialBase(BaseModel):
    type: str = Field(..., min_length=1, max_length=100)
    balance: int = Field(..., ge=0)
    price: int = Field(..., gt=0)
class MaterialCreate(MaterialBase): pass
class MaterialUpdate(BaseModel):
    type: Optional[str] = Field(None, min_length=1, max_length=100)
    balance: Optional[int] = Field(None, ge=0)
    price: Optional[int] = Field(None, gt=0)
class Material(MaterialBase, BaseEntity): pass

# --- Order ---
class OrderBase(BaseModel):
    client_id: str
    worker_id: Optional[str] = None
    prod_period: Optional[int] = Field(None, gt=0)
    status: OrderStatus = OrderStatus.PROCESSING
# ForwardRef для 순환 зависимостей с MaterialOnOrderCreate
class MaterialOnOrderCreate(BaseModel):
    material_id: str
    amount: int = Field(..., gt=0)
class OrderCreate(OrderBase):
    materials: List[MaterialOnOrderCreate] = []
class OrderUpdate(BaseModel):
    client_id: Optional[str] = None
    worker_id: Optional[str] = None
    prod_period: Optional[int] = Field(None, gt=0)
    status: Optional[OrderStatus] = None
# ForwardRef для 순환 зависимостей с MaterialOnOrder
class MaterialOnOrder(BaseEntity): # Полная модель MaterialOnOrder нужна здесь
    order_id: str
    material_id: str
    amount: int = Field(..., gt=0)
    material: Optional[Material] = None # Детали материала
class Order(OrderBase, BaseEntity):
    date: datetime
    client: Optional[Client] = None # Связанные данные
    worker: Optional[Worker] = None
    materials_on_order: List[MaterialOnOrder] = []

# --- MaterialOnOrder --- (Полные модели)
class MaterialOnOrderBase(BaseModel):
    order_id: str
    material_id: str
    amount: int = Field(..., gt=0)
# Create модель уже определена выше
class MaterialOnOrderUpdate(BaseModel):
    amount: Optional[int] = Field(None, gt=0) # Обычно меняем только кол-во
# Read модель MaterialOnOrder уже определена выше

# --- MaterialProvider ---
class MaterialProviderBase(BaseModel):
    provider_id: str
    material_id: str
class MaterialProviderCreate(MaterialProviderBase): pass
class MaterialProviderUpdate(BaseModel): pass # Обычно не обновляется, а удаляется/создается заново
class MaterialProvider(MaterialProviderBase, BaseEntity):
     provider: Optional[Provider] = None
     material: Optional[Material] = None


# --- Модель для входа ---
class LoginRequest(BaseModel):
    phone: str
    password: str

# --- Модель для ответа с данными пользователя после логина ---
class AuthenticatedUser(BaseModel):
     user_type: str # 'client' или 'worker'
     user_data: Client | Worker # Данные конкретного пользователя (без хеша пароля)