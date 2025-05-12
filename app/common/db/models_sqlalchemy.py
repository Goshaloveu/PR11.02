# models_sqlalchemy.py
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
from .models_pydantic import OrderStatus # Используем только Enum из Pydantic

class Client(Base):
    __tablename__ = 'clients'
    id = Column(String(36), primary_key=True, index=True)
    first = Column(String(100), nullable=False)
    last = Column(String(100), nullable=False)
    middle = Column(String(100), nullable=True)
    phone = Column(String(12), nullable=True, index=True)
    mail = Column(String(200), nullable=True, index=True)
    # Добавленные поля для аутентификации
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    # ---
    date = Column(DateTime, nullable=False, server_default=func.now())
    orders = relationship("Order", back_populates="client")
    def __repr__(self): return f"<Client(id='{self.id}', username='{self.username}')>"

class Worker(Base):
    __tablename__ = 'workers'
    id = Column(String(36), primary_key=True, index=True)
    first = Column(String(100), nullable=False)
    last = Column(String(100), nullable=True)
    middle = Column(String(100), nullable=True)
    phone = Column(String(12), nullable=True, index=True)
    mail = Column(String(200), nullable=True, index=True)
    # Добавленные поля для аутентификации
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    # ---
    date = Column(DateTime, nullable=False, server_default=func.now())
    pass_series = Column(String(4), nullable=True)
    pass_number = Column(String(6), nullable=True)
    position = Column(String(200), nullable=False)
    born_date = Column(DateTime, nullable=True)
    assigned_orders = relationship("Order", back_populates="worker")
    def __repr__(self): return f"<Worker(id='{self.id}', username='{self.username}')>"

# --- Provider, Material, Order, MaterialOnOrder, MaterialProvider ---
# --- Остаются БЕЗ ИЗМЕНЕНИЙ --- (Скопируйте из предыдущего ответа)
class Provider(Base):
    __tablename__ = 'providers'
    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    inn = Column(String(12), nullable=False, unique=True)
    phone = Column(String(12), nullable=True)
    mail = Column(String(200), nullable=True)
    address = Column(String(200), nullable=True)
    materials = relationship("Material", secondary="mat_provider", back_populates="providers")
    def __repr__(self): return f"<Provider(id='{self.id}', name='{self.name}')>"

class Material(Base):
    __tablename__ = 'materials'
    id = Column(String(36), primary_key=True, index=True)
    type = Column(String(100), nullable=False, index=True)
    balance = Column(Integer, nullable=False, default=0)
    price = Column(Integer, nullable=False)
    providers = relationship("Provider", secondary="mat_provider", back_populates="materials")
    orders_link = relationship("MaterialOnOrder", back_populates="material")
    def __repr__(self): return f"<Material(id='{self.id}', type='{self.type}', balance={self.balance})>"

class Order(Base):
    __tablename__ = 'orders'
    id = Column(String(36), primary_key=True, index=True)
    client_id = Column(String(36), ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, name='client')
    worker_id = Column(String(36), ForeignKey('workers.id', ondelete='SET NULL'), nullable=True, name='worker')
    date = Column(DateTime, nullable=False, server_default=func.now())
    prod_period = Column(Integer, nullable=True)
    status = Column(SQLEnum(OrderStatus, name='order_status_enum'), nullable=False, default=OrderStatus.PROCESSING)
    client = relationship("Client", back_populates="orders")
    worker = relationship("Worker", back_populates="assigned_orders")
    materials_link = relationship("MaterialOnOrder", back_populates="order", cascade="all, delete-orphan")
    def __repr__(self): return f"<Order(id='{self.id}', client_id='{self.client_id}', status='{self.status.value}')>"

class MaterialOnOrder(Base):
    __tablename__ = 'mat_on_order'
    id = Column(String(36), primary_key=True, index=True)
    order_id = Column(String(36), ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, name='order')
    material_id = Column(String(36), ForeignKey('materials.id', ondelete='CASCADE'), nullable=False, name='material')
    amount = Column(Integer, nullable=False)
    order = relationship("Order", back_populates="materials_link")
    material = relationship("Material", back_populates="orders_link")
    def __repr__(self): return f"<MatOnOrder(order='{self.order_id}', material='{self.material_id}', amount={self.amount})>"

class MaterialProvider(Base):
    __tablename__ = 'mat_provider'
    id = Column(String(36), primary_key=True, index=True)
    provider_id = Column(String(36), ForeignKey('providers.id', ondelete='CASCADE'), nullable=False, name='provider')
    material_id = Column(String(36), ForeignKey('materials.id', ondelete='CASCADE'), nullable=False, name='material')
    def __repr__(self): return f"<MatProvider(provider='{self.provider_id}', material='{self.material_id}')>"