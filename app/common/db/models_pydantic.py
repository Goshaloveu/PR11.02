# models_pydantic.py
import re
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator, EmailStr
from enum import Enum
from .utils import UUIDUtils # Импортируем твой класс

# --- Константы и валидаторы --- (Оставляем как есть)
NAME_REGEX = r'^[а-яА-Яёa-zA-Z-]+$'
# Обновляем формат телефона, чтобы соответствовать regex в базе данных
PHONE_REGEX = r'^\+?[0-9 -()]{7,25}$'
INN_REGEX = r'^[0-9]{10,12}$'
PASS_SERIES_REGEX = r'^[0-9]{4}$'
PASS_NUMBER_REGEX = r'^[0-9]{6}$'

def validate_regex(value: Optional[str], pattern: str, field_name: str) -> Optional[str]:
    if value is None: return value
    if not re.match(pattern, value):
        raise ValueError(f'{field_name} format is invalid ("{value}")')
    return value

# Функция для извлечения последних 10 цифр телефона
def extract_phone_digits(phone: Optional[str]) -> Optional[str]:
    if not phone: return phone
    
    # Оставляем номер как есть, но проверяем, соответствует ли он формату
    if re.match(PHONE_REGEX, phone):
        return phone
        
    # В старом формате: извлекаем только цифры из номера телефона
    digits = re.sub(r'[^0-9]', '', phone)
    
    # Если номер без + и начинается с 8, преобразуем в +7
    if digits.startswith('8') and len(digits) >= 11:
        return f"+7{digits[1:]}"
        
    # Если просто цифры, добавляем +
    if digits and not phone.startswith('+'):
        return f"+{digits}"
        
    # В других случаях возвращаем как есть
    return phone

# --- Enum ---
class OrderStatus(str, Enum):
    PROCESSING = 'Обработка'
    IN_PROGRESS = 'В работе'
    COMPLETED = 'Выполнен'

# --- Базовая модель ---
class BaseEntity(BaseModel):
     id: str = Field(default_factory=UUIDUtils.getUUID)
     class Config:
        from_attributes = True
        populate_by_name = True
        # Позволяет доступ как через .id, так и через .id_
        field_aliases = {"id": "id_"}

# --- Модели данных ---

# --- Client ---
class ClientBase(BaseModel):
    # Основные поля
    first: str = Field(..., min_length=1, max_length=100)
    last: str = Field(..., min_length=1, max_length=100)
    middle: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=25)  # Увеличиваем до 25
    mail: Optional[EmailStr] = Field(None, max_length=200)

    # Валидаторы
    @field_validator('first', 'last')
    def validate_names(cls, v): return validate_regex(v, NAME_REGEX, 'Name')
    @field_validator('middle')
    def validate_middle_name(cls, v): return validate_regex(v, NAME_REGEX, 'Middle Name') if v else v
    @field_validator('phone')
    def validate_phone_format(cls, v):
        # Обновленная логика валидации телефона
        if not v: return v
        # Если уже соответствует формату, оставляем как есть
        if re.match(PHONE_REGEX, v):
            return v
        # Если не соответствует, пытаемся преобразовать
        return extract_phone_digits(v)

class ClientCreate(ClientBase):
    password: str = Field(..., min_length=6) # Пароль обязателен при создании

class ClientUpdate(BaseModel): # Отдельная модель для обновления
    first: Optional[str] = Field(None, min_length=1, max_length=100)
    last: Optional[str] = Field(None, min_length=1, max_length=100)
    middle: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=25)  # Увеличиваем до 25
    mail: Optional[EmailStr] = Field(None, max_length=200)
    password: Optional[str] = Field(None, min_length=6) # Для смены пароля

    # Валидаторы применяются, если поле передано
    @field_validator('first', 'last', mode='before')
    def check_names_update(cls, v): return validate_regex(v, NAME_REGEX, 'Name') if v else v
    @field_validator('middle', mode='before')
    def check_middle_update(cls, v): return validate_regex(v, NAME_REGEX, 'Middle Name') if v else v
    @field_validator('phone', mode='before')
    def check_phone_update(cls, v): return validate_regex(v, PHONE_REGEX, 'Phone') if v else v

class Client(ClientBase, BaseEntity): # Модель для чтения из БД
    date: datetime
    # НЕ СОДЕРЖИТ HASHED_PASSWORD для безопасности

# --- Worker ---
class WorkerBase(BaseModel):
    first: str = Field(..., min_length=1, max_length=100)
    last: str = Field(..., min_length=1, max_length=100)
    middle: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=25)  # Увеличиваем до 25
    mail: Optional[EmailStr] = Field(None, max_length=200)
    pass_series: Optional[str] = Field(None, max_length=4)
    pass_number: Optional[str] = Field(None, max_length=6)
    position: str = Field(..., min_length=1, max_length=200)
    born_date: Optional[datetime] = None

    # Валидаторы
    @field_validator('first', 'last')
    def validate_worker_names(cls, v): return validate_regex(v, NAME_REGEX, 'Name part')
    @field_validator('middle')
    def validate_worker_middle(cls, v): return validate_regex(v, NAME_REGEX, 'Middle name') if v else v
    @field_validator('phone')
    def validate_worker_phone(cls, v): 
        # Обновленная логика валидации телефона
        if not v: return v
        # Если уже соответствует формату, оставляем как есть
        if re.match(PHONE_REGEX, v):
            return v
        # Если не соответствует, пытаемся преобразовать
        return extract_phone_digits(v)
    @field_validator('pass_series')
    def validate_pass_series(cls, v): return validate_regex(v, PASS_SERIES_REGEX, 'Passport Series') if v else v
    @field_validator('pass_number')
    def validate_pass_number(cls, v): return validate_regex(v, PASS_NUMBER_REGEX, 'Passport Number') if v else v

class WorkerCreate(WorkerBase):
    password: str = Field(..., min_length=6)

class WorkerUpdate(BaseModel): # Отдельная модель
    first: Optional[str] = Field(None, min_length=1, max_length=100)
    last: Optional[str] = Field(None, max_length=100)
    middle: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=25)  # Увеличиваем до 25
    mail: Optional[EmailStr] = Field(None, max_length=200)
    pass_series: Optional[str] = Field(None, max_length=4)
    pass_number: Optional[str] = Field(None, max_length=6)
    position: Optional[str] = Field(None, min_length=1, max_length=200)
    born_date: Optional[datetime] = None
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

class Worker(WorkerBase, BaseEntity):
    date: datetime
    # НЕ СОДЕРЖИТ HASHED_PASSWORD

# --- Provider ---
class ProviderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    inn: str = Field(..., max_length=12)
    phone: Optional[str] = Field(None, max_length=25)  # Увеличиваем длину до 25
    mail: Optional[EmailStr] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=200)
    @field_validator('inn')
    def validate_inn_format(cls, v): return validate_regex(v, INN_REGEX, 'INN')
    @field_validator('phone')
    def validate_provider_phone(cls, v): 
        # Просто проверяем, что телефон содержит только цифры
        if v is None:
            return v
        # Проверяем, что телефон содержит только цифры, и длина 10
        if not v.isdigit():
            raise ValueError(f"Phone must contain only digits (got: '{v}')")
        return v

class ProviderCreate(ProviderBase): pass

class ProviderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    inn: Optional[str] = Field(None, max_length=12)
    phone: Optional[str] = Field(None, max_length=25)  # Увеличиваем длину до 25
    mail: Optional[EmailStr] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=200)
    # Валидаторы
    @field_validator('inn', mode='before')
    def check_inn_update(cls, v): return validate_regex(v, INN_REGEX, 'INN') if v else v
    @field_validator('phone', mode='before')
    def check_provider_phone_update(cls, v): 
        # Просто проверяем, что телефон содержит только цифры
        if v is None:
            return v
        # Проверяем, что телефон содержит только цифры
        if not v.isdigit():
            raise ValueError(f"Phone must contain only digits (got: '{v}')")
        return v

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
# ForwardRef для циклических зависимостей с MaterialOnOrderCreate
class MaterialOnOrderCreate(BaseModel):
    material_id: str
    amount: int = Field(..., gt=0)
class OrderCreate(OrderBase):
    materials: List[MaterialOnOrderCreate] = []
    date: Optional[datetime] = None
class OrderUpdate(BaseModel):
    client_id: Optional[str] = None
    worker_id: Optional[str] = None
    prod_period: Optional[int] = Field(None, gt=0)
    status: Optional[OrderStatus] = None
# ForwardRef для циклических зависимостей с MaterialOnOrder
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
    services: List[Any] = []  # Add services attribute with empty list default

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
    user_type: str = "client"  # Default to client login
    
    @field_validator('phone')
    def validate_login_phone(cls, v):
        """Extract just the last 10 digits from the phone number"""
        if not v: return v
        digits = re.sub(r'[^0-9]', '', v)
        if len(digits) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        return digits[-10:]  # Return only last 10 digits

# --- Модель для ответа с данными пользователя после логина ---
class AuthenticatedUser(BaseModel):
     user_type: str # 'client' или 'worker'
     user_data: dict  # Принимаем данные как словарь для простоты