# dao.py
from abc import ABC, abstractmethod
from typing import List, Optional, Type, TypeVar, Generic, Any, Dict
from pydantic import BaseModel
import logging # Для логгирования ошибок

# Настройка логгера
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Дженерик тип для моделей Pydantic
T = TypeVar('T', bound=BaseModel)

class DaoBase(Generic[T], ABC):
    """ Базовый класс DAO """

    def __init__(self, db_connection: Any, model_cls: Type[T]):
        """
        Инициализация DAO.
        db_connection: Активное соединение с базой данных (зависит от библиотеки)
        model_cls: Класс Pydantic модели, с которой работает DAO
        """
        self.db_connection = db_connection
        self._model_cls = model_cls
        # Курсор обычно создается перед выполнением запроса
        # self.cursor = self.db_connection.cursor()

    @property
    @abstractmethod
    def table_name(self) -> str:
        """ Должен вернуть имя таблицы в БД """
        pass

    def _execute_query(self, query: str, params: tuple = None) -> Any:
        """ Вспомогательный метод для выполнения запроса """
        # Реализация зависит от драйвера БД
        # Пример для sqlite3:
        # try:
        #     cursor = self.db_connection.cursor()
        #     cursor.execute(query, params or ())
        #     self.db_connection.commit() # Для INSERT, UPDATE, DELETE
        #     return cursor
        # except Exception as e:
        #     logging.error(f"DB Error executing query '{query[:50]}...': {e}")
        #     self.db_connection.rollback() # Откатить изменения при ошибке
        #     raise # Перевыбросить исключение для обработки выше
        raise NotImplementedError("Нужно реализовать _execute_query в зависимости от драйвера БД")

    def _map_row_to_model(self, row: tuple, column_names: List[str]) -> Optional[T]:
        """ Преобразует строку результата запроса в Pydantic модель """
        if not row:
            return None
        try:
            data = dict(zip(column_names, row))
            # Обработка Enum, если необходимо (Pydantic v2 может делать это лучше)
            if 'status' in data and hasattr(self._model_cls, 'status') and issubclass(self._model_cls.__fields__['status'].type_, Enum):
                 data['status'] = OrderStatus(data['status']) # Пример для OrderStatus
            return self._model_cls(**data)
        except Exception as e:
            logging.error(f"Error mapping row to model {self._model_cls.__name__}: {e} | Row: {row}")
            return None

    def get_by_id(self, entity_id: str) -> Optional[T]:
        """ Получить запись по ID """
        # ВАЖНО: Имена колонок должны совпадать с полями модели Pydantic
        # Или нужно настроить маппинг в _map_row_to_model
        query = f"SELECT * FROM {self.table_name} WHERE id = ?" # Используйте плейсхолдер вашей БД (?, %s)
        try:
            # cursor = self._execute_query(query, (entity_id,))
            # column_names = [desc[0] for desc in cursor.description]
            # row = cursor.fetchone()
            # return self._map_row_to_model(row, column_names)
            logging.info(f"DAO: Executing get_by_id for {self.table_name} with id={entity_id}")
            # ЗАГЛУШКА - замените реальным вызовом _execute_query
            print(f"Executing SQL (Conceptual): {query} with params ({entity_id},)")
            return None # Заглушка
        except Exception as e:
            logging.error(f"DAO Error in get_by_id for {self.table_name}: {e}")
            return None

    def list_all(self) -> List[T]:
        """ Получить все записи из таблицы """
        query = f"SELECT * FROM {self.table_name}"
        entities = []
        try:
            # cursor = self._execute_query(query)
            # column_names = [desc[0] for desc in cursor.description]
            # rows = cursor.fetchall()
            # for row in rows:
            #     model = self._map_row_to_model(row, column_names)
            #     if model:
            #         entities.append(model)
            logging.info(f"DAO: Executing list_all for {self.table_name}")
            # ЗАГЛУШКА - замените реальным вызовом _execute_query
            print(f"Executing SQL (Conceptual): {query}")
            return [] # Заглушка
        except Exception as e:
            logging.error(f"DAO Error in list_all for {self.table_name}: {e}")
            return []

    def add(self, entity: T) -> bool:
        """ Добавить новую запись """
        # Pydantic v2: entity.model_dump()
        # Pydantic v1: entity.dict()
        data = entity.model_dump(exclude_unset=True) # Исключаем поля None, если не заданы явно
        # Корректируем имена полей (если в БД client, а в модели client_id)
        if 'client_id' in data: data['client'] = data.pop('client_id')
        if 'worker_id' in data: data['worker'] = data.pop('worker_id')
        if 'order_id' in data: data['order'] = data.pop('order_id')
        if 'material_id' in data: data['material'] = data.pop('material_id')
        if 'provider_id' in data: data['provider'] = data.pop('provider_id')

        # Преобразуем Enum в строку для БД, если Pydantic еще не сделал это
        if 'status' in data and isinstance(data['status'], Enum):
            data['status'] = data['status'].value

        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data)) # Используйте плейсхолдер вашей БД (?, %s)
        values = tuple(data.values())
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        try:
            # self._execute_query(query, values)
            logging.info(f"DAO: Executing add for {self.table_name}")
            # ЗАГЛУШКА - замените реальным вызовом _execute_query
            print(f"Executing SQL (Conceptual): {query} with params {values}")
            return True # Заглушка
        except Exception as e:
            logging.error(f"DAO Error in add for {self.table_name}: {e}")
            return False

    def update(self, entity: T) -> bool:
        """ Обновить существующую запись по ID """
        if not entity.id:
             logging.error(f"DAO Error in update for {self.table_name}: ID is missing")
             return False

        data = entity.model_dump(exclude={'id'}, exclude_unset=True) # Исключаем id и не установленные
        # Корректируем имена полей (если в БД client, а в модели client_id)
        if 'client_id' in data: data['client'] = data.pop('client_id')
        if 'worker_id' in data: data['worker'] = data.pop('worker_id')
        if 'order_id' in data: data['order'] = data.pop('order_id')
        if 'material_id' in data: data['material'] = data.pop('material_id')
        if 'provider_id' in data: data['provider'] = data.pop('provider_id')

        # Преобразуем Enum в строку для БД
        if 'status' in data and isinstance(data['status'], Enum):
             data['status'] = data['status'].value

        set_clause = ', '.join([f"{key} = ?" for key in data.keys()]) # Используйте плейсхолдер вашей БД (?, %s)
        values = tuple(data.values()) + (entity.id,)
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"

        try:
            # self._execute_query(query, values)
            logging.info(f"DAO: Executing update for {self.table_name} with id={entity.id}")
             # ЗАГЛУШКА - замените реальным вызовом _execute_query
            print(f"Executing SQL (Conceptual): {query} with params {values}")
            return True # Заглушка
        except Exception as e:
            logging.error(f"DAO Error in update for {self.table_name}: {e}")
            return False

    def delete(self, entity_id: str) -> bool:
        """ Удалить запись по ID """
        query = f"DELETE FROM {self.table_name} WHERE id = ?" # Используйте плейсхолдер вашей БД (?, %s)
        try:
            # self._execute_query(query, (entity_id,))
            logging.info(f"DAO: Executing delete for {self.table_name} with id={entity_id}")
             # ЗАГЛУШКА - замените реальным вызовом _execute_query
            print(f"Executing SQL (Conceptual): {query} with params ({entity_id},)")
            return True # Заглушка
        except Exception as e:
            logging.error(f"DAO Error in delete for {self.table_name}: {e}")
            return False

    # Можно добавить методы list_by, list_like, batch операции по аналогии с твоим примером

# --- Конкретные реализации DAO ---
# Импортируем модели из models.py
from .models import Client, Order, Worker, Provider, Material, MaterialOnOrder, MaterialProvider, OrderStatus, Enum

class ClientDao(DaoBase[Client]):
    table_name = 'clients'
    def __init__(self, db_connection: Any):
        super().__init__(db_connection, Client)

class OrderDao(DaoBase[Order]):
    table_name = 'orders'
    def __init__(self, db_connection: Any):
        super().__init__(db_connection, Order)
    # Можно добавить специфичные методы, например, поиск по статусу или клиенту
    def find_by_status(self, status: OrderStatus) -> List[Order]:
        query = f"SELECT * FROM {self.table_name} WHERE status = ?"
        entities = []
        try:
            logging.info(f"DAO: Executing find_by_status for {self.table_name} with status={status.value}")
            # ЗАГЛУШКА - замените реальным вызовом _execute_query
            print(f"Executing SQL (Conceptual): {query} with params ('{status.value}',)")
            # cursor = self._execute_query(query, (status.value,))
            # ... (логика fetchall и маппинга) ...
            return [] # Заглушка
        except Exception as e:
            logging.error(f"DAO Error in find_by_status for {self.table_name}: {e}")
            return []

class WorkerDao(DaoBase[Worker]):
    table_name = 'workers'
    def __init__(self, db_connection: Any):
        super().__init__(db_connection, Worker)

class ProviderDao(DaoBase[Provider]):
    table_name = 'providers'
    def __init__(self, db_connection: Any):
        super().__init__(db_connection, Provider)

class MaterialDao(DaoBase[Material]):
    table_name = 'materials'
    def __init__(self, db_connection: Any):
        super().__init__(db_connection, Material)

    # Пример специфичного метода: обновление остатка
    def update_balance(self, material_id: str, change: int) -> bool:
        """ Изменяет баланс материала (change может быть отрицательным) """
        # ВАЖНО: Сделать эту операцию атомарной в реальном приложении
        # (проверка >= 0 и обновление в одной транзакции)
        query = f"UPDATE {self.table_name} SET balance = balance + ? WHERE id = ? AND balance + ? >= 0"
        try:
            logging.info(f"DAO: Executing update_balance for {self.table_name} with id={material_id}, change={change}")
            # ЗАГЛУШКА - замените реальным вызовом _execute_query
            print(f"Executing SQL (Conceptual): {query} with params ({change}, {material_id}, {change})")
            # cursor = self._execute_query(query, (change, material_id, change))
            # return cursor.rowcount > 0 # Проверяем, была ли строка обновлена
            return True # Заглушка
        except Exception as e:
            logging.error(f"DAO Error updating balance for material {material_id}: {e}")
            return False


class MaterialOnOrderDao(DaoBase[MaterialOnOrder]):
    table_name = 'mat_on_order'
    def __init__(self, db_connection: Any):
        super().__init__(db_connection, MaterialOnOrder)

    def find_by_order_id(self, order_id: str) -> List[MaterialOnOrder]:
        query = f"SELECT * FROM {self.table_name} WHERE \"order\" = ?" # "order" - ключевое слово, берем в кавычки
        entities = []
        try:
             logging.info(f"DAO: Executing find_by_order_id for {self.table_name} with order_id={order_id}")
             # ЗАГЛУШКА - замените реальным вызовом _execute_query
             print(f"Executing SQL (Conceptual): {query} with params ('{order_id}',)")
             # cursor = self._execute_query(query, (order_id,))
             # ... (логика fetchall и маппинга) ...
             return [] # Заглушка
        except Exception as e:
            logging.error(f"DAO Error in find_by_order_id for {self.table_name}: {e}")
            return []


class MaterialProviderDao(DaoBase[MaterialProvider]):
    table_name = 'mat_provider'
    def __init__(self, db_connection: Any):
        super().__init__(db_connection, MaterialProvider)
    # Можно добавить методы поиска по provider_id или material_id