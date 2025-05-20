# models_sqlalchemy.py
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Index, CheckConstraint
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
    date = Column(DateTime, nullable=False, server_default=func.now())
    hash_password = Column(String(255), nullable=False)
    orders = relationship("Order", back_populates="client")

    __table_args__ = (
        CheckConstraint("first REGEXP '^[а-яА-Яёa-zA-Z-]*$'", name="check_first"),
        CheckConstraint("last REGEXP '^[а-яА-Яёa-zA-Z-]*$'", name="check_last"),
        CheckConstraint("middle REGEXP '^[а-яА-Яёa-zA-Z-]*$'", name="check_middle"),
        CheckConstraint("phone REGEXP '^\\+7[0-9]{10}$|^8[0-9]{10}$'", name="check_phone"),
        CheckConstraint("mail REGEXP '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'", name="check_mail"),
    )
    
    def __repr__(self): return f"<Client(id='{self.id}', name='{self.first} {self.last}')>"

class Worker(Base):
    __tablename__ = 'workers'
    id = Column(String(36), primary_key=True, index=True)
    first = Column(String(100), nullable=False)
    last = Column(String(100), nullable=False)
    middle = Column(String(100), nullable=True)
    phone = Column(String(12), nullable=True, index=True)
    mail = Column(String(200), nullable=True, index=True)
    date = Column(DateTime, nullable=False, server_default=func.now())
    pass_series = Column(String(4), nullable=True)
    pass_number = Column(String(6), nullable=True)
    position = Column(String(200), nullable=False)
    born_date = Column(DateTime, nullable=True)
    hash_password = Column(String(255), nullable=False)
    assigned_orders = relationship("Order", back_populates="worker")

    __table_args__ = (
        CheckConstraint("first REGEXP '^[а-яА-Яёa-zA-Z-]*$'", name="check_worker_first"),
        CheckConstraint("last REGEXP '^[а-яА-Яёa-zA-Z-]*$'", name="check_worker_last"),
        CheckConstraint("middle REGEXP '^[а-яА-Яёa-zA-Z-]*$'", name="check_worker_middle"),
        CheckConstraint("phone REGEXP '^\\+7[0-9]{10}$|^8[0-9]{10}$'", name="check_worker_phone"),
        CheckConstraint("mail REGEXP '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'", name="check_worker_mail"),
        CheckConstraint("pass_series REGEXP '^[0-9]{4}$'", name="check_worker_pass_series"),
        CheckConstraint("pass_number REGEXP '^[0-9]{6}$'", name="check_worker_pass_number"),
    )
    
    def __repr__(self): return f"<Worker(id='{self.id}', name='{self.first} {self.last}', position='{self.position}')>"

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

    __table_args__ = (
        CheckConstraint("inn REGEXP '^[0-9]{10,12}$'", name="check_provider_inn"),
        CheckConstraint("phone REGEXP '^\\+?[0-9 -()]{7,25}$'", name="check_provider_phone"),
        CheckConstraint("mail REGEXP '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'", name="check_provider_mail"),
    )
    
    def __repr__(self): return f"<Provider(id='{self.id}', name='{self.name}')>"

class Material(Base):
    __tablename__ = 'materials'
    id = Column(String(36), primary_key=True, index=True)
    type = Column(String(100), nullable=False, index=True)
    balance = Column(Integer, nullable=False, default=0)
    price = Column(Integer, nullable=False)
    providers = relationship("Provider", secondary="mat_provider", back_populates="materials")
    orders_link = relationship("MaterialOnOrder", back_populates="material")

    __table_args__ = (
        CheckConstraint("balance >= 0", name="check_material_balance"),
        CheckConstraint("price > 0", name="check_material_price"),
    )
    
    def __repr__(self): return f"<Material(id='{self.id}', type='{self.type}', balance={self.balance})>"

class Order(Base):
    __tablename__ = 'orders'
    id = Column(String(36), primary_key=True, index=True)
    client_id = Column(String(36), ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, name='client')
    worker_id = Column(String(36), ForeignKey('workers.id', ondelete='SET NULL'), nullable=True, name='worker')
    date = Column(DateTime, nullable=False, server_default=func.now())
    prod_period = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False, default=OrderStatus.PROCESSING.value)
    client = relationship("Client", back_populates="orders")
    worker = relationship("Worker", back_populates="assigned_orders")
    materials_link = relationship("MaterialOnOrder", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("prod_period > 0", name="check_order_prod_period"),
        CheckConstraint("status in ('Обработка', 'В работе', 'Выполнен')", name="check_order_status"),
    )
    
    def __repr__(self): return f"<Order(id='{self.id}', client_id='{self.client_id}', status='{self.status}')>"

class MaterialOnOrder(Base):
    __tablename__ = 'mat_on_order'
    id = Column(String(36), primary_key=True, index=True)
    order_id = Column(String(36), ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, name='order')
    material_id = Column(String(36), ForeignKey('materials.id', ondelete='CASCADE'), nullable=False, name='material')
    amount = Column(Integer, nullable=False)
    order = relationship("Order", back_populates="materials_link")
    material = relationship("Material", back_populates="orders_link")

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_mat_order_amount"),
    )
    
    def __repr__(self): return f"<MatOnOrder(order='{self.order_id}', material='{self.material_id}', amount={self.amount})>"

class MaterialProvider(Base):
    __tablename__ = 'mat_provider'
    id = Column(String(36), primary_key=True, index=True)
    provider_id = Column(String(36), ForeignKey('providers.id', ondelete='CASCADE'), nullable=False, name='provider')
    material_id = Column(String(36), ForeignKey('materials.id', ondelete='CASCADE'), nullable=False, name='material')
    
    def __repr__(self): return f"<MatProvider(provider='{self.provider_id}', material='{self.material_id}')>"