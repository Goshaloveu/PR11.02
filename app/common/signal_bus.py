# utils/signal_bus.py
from PyQt6.QtCore import QObject, pyqtSignal
from .singleton import qsingleton

@qsingleton
class SignalBus(QObject):
    """ Signal bus for the Jewelry Shop application """

    def __init__(self):
        super().__init__()
        print("SignalBus initialized")

    # --- Сигналы об ошибках и общие ---
    error_occurred = pyqtSignal(str)
    status_message = pyqtSignal(str)
    database_error = pyqtSignal(str)

    # --- Сигналы аутентификации ---
    login_successful = pyqtSignal(str, dict) # Тип пользователя ('client'/'worker'), данные пользователя
    login_failed = pyqtSignal(str)          # Причина ошибки
    logout_completed = pyqtSignal()         # Сигнал о выходе

    # --- Сигналы CRUD (Полный список) ---

    # Clients
    client_created = pyqtSignal(dict)
    client_updated = pyqtSignal(dict)
    client_deleted = pyqtSignal(str) # id

    # Workers
    worker_created = pyqtSignal(dict)
    worker_updated = pyqtSignal(dict)
    worker_deleted = pyqtSignal(str) # id

    # Providers
    provider_created = pyqtSignal(dict)
    provider_updated = pyqtSignal(dict)
    provider_deleted = pyqtSignal(str) # id

    # Materials
    material_created = pyqtSignal(dict)
    material_updated = pyqtSignal(dict)
    material_deleted = pyqtSignal(str) # id
    material_balance_changed = pyqtSignal(str, int) # material_id, new_balance

    # Orders
    order_created = pyqtSignal(dict)
    order_updated = pyqtSignal(dict)
    order_deleted = pyqtSignal(str) # id
    order_status_changed = pyqtSignal(str, str) # order_id, new_status_value

    # MaterialOnOrder (Связи) - сигналы могут быть менее нужны, т.к. управляются через заказ
    material_linked_to_order = pyqtSignal(dict) # Данные MaterialOnOrder
    material_unlinked_from_order = pyqtSignal(str) # id MaterialOnOrder

    # MaterialProvider (Связи)
    material_linked_to_provider = pyqtSignal(dict) # Данные MaterialProvider
    material_unlinked_from_provider = pyqtSignal(str) # id MaterialProvider
        
signalbus = SignalBus()