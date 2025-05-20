from PyQt6.QtWidgets import (
    QMainWindow, QFrame, QHBoxLayout, QVBoxLayout, 
    QStackedWidget, QWidget, QApplication, QLabel, 
    QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSlot
from PyQt6.QtGui import QFont, QIcon

from qfluentwidgets import (
    NavigationInterface, NavigationItemPosition, 
    NavigationWidget, isDarkTheme, setTheme, Theme,
    FluentIcon, InfoBar, FluentWindow
)

from ...common.signal_bus import signalBus
from .profile_interface import ProfileInterface
from .create_order_interface import CreateOrderInterface
from .orders_interface import OrdersInterface
from .materials_interface import MaterialsInterface
from .suppliers_interface import SuppliersInterface
from .employees_interface import EmployeesInterface
from .settings_interface import SettingsInterface


# Временная заглушка для DashboardInterface, если его нет в коде
class DashboardInterface(QWidget):
    def __init__(self, user_data, parent=None):
        super().__init__(parent=parent)
        self.user_data = user_data
        layout = QVBoxLayout(self)
        welcome_label = QLabel(f"Добро пожаловать, {user_data.get('first', '')} {user_data.get('last', '')}!")
        welcome_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(welcome_label)
        layout.addStretch()


class WorkerWindow(FluentWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.setWindowTitle("Terra - Кабинет сотрудника")
        # self.resize(1100, 750) # Commented out fixed size
        
        # Adaptive sizing
        screen = QApplication.primaryScreen().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()

        # Define desired proportions and limits
        desired_width = int(screen_width * 0.8)
        desired_height = int(screen_height * 0.8)

        # Clamp to min/max sizes
        min_w, min_h = 900, 650 # Minimum window size
        max_w, max_h = 1300, 900 # Maximum initial window size (can be resized larger by user)

        initial_width = max(min_w, min(desired_width, max_w))
        initial_height = max(min_h, min(desired_height, max_h))

        self.resize(initial_width, initial_height)
        self.setMinimumSize(min_w, min_h)
        
        # Устанавливаем светлую тему для приложения
        setTheme(Theme.LIGHT)
        
        # Исправление ошибки QBackingStore::endPaint() - уничтожаем QPainter перед закрытием окна
        self.destroyed.connect(self._cleanup_resources)
        
        # Connect signals
        self._connect_signals()
        
        # Создаем интерфейсы перед настройкой навигации
        self._create_interfaces()
        
        # Set up navigation
        self._setup_navigation()
        
        # Центрируем окно на экране
        self._center_window()
        
        # Show welcome message
        self._show_welcome_message()
        
    def _cleanup_resources(self):
        """Метод для очистки ресурсов перед закрытием окна"""
        # Этот метод вызывается при уничтожении окна и решает проблему с QBackingStore::endPaint()
        # Принудительно освобождаем ресурсы интерфейсов
        # Cleanup interfaces
        if hasattr(self, 'profile_interface') and self.profile_interface is not None:
            self.profile_interface.setParent(None)
            self.profile_interface = None
        if hasattr(self, 'create_order_interface') and self.create_order_interface is not None:
            self.create_order_interface.setParent(None)
            self.create_order_interface = None
        if hasattr(self, 'orders_interface') and self.orders_interface is not None:
            self.orders_interface.setParent(None)
            self.orders_interface = None
        if hasattr(self, 'materials_interface') and self.materials_interface is not None:
            self.materials_interface.setParent(None)
            self.materials_interface = None
        if hasattr(self, 'suppliers_interface') and self.suppliers_interface is not None:
            self.suppliers_interface.setParent(None)
            self.suppliers_interface = None
        if hasattr(self, 'employees_interface') and self.employees_interface is not None:
            self.employees_interface.setParent(None)
            self.employees_interface = None
        if hasattr(self, 'settings_interface') and self.settings_interface is not None:
            self.settings_interface.setParent(None)
            self.settings_interface = None
        if hasattr(self, 'dashboard_interface') and self.dashboard_interface is not None:
            self.dashboard_interface.setParent(None)
            self.dashboard_interface = None

        # Cleanup containers
        if hasattr(self, 'profile_container') and self.profile_container is not None:
            self.profile_container.setParent(None)
            self.profile_container = None
        if hasattr(self, 'create_order_container') and self.create_order_container is not None:
            self.create_order_container.setParent(None)
            self.create_order_container = None
        if hasattr(self, 'orders_container') and self.orders_container is not None:
            self.orders_container.setParent(None)
            self.orders_container = None
        if hasattr(self, 'materials_container') and self.materials_container is not None:
            self.materials_container.setParent(None)
            self.materials_container = None
        if hasattr(self, 'suppliers_container') and self.suppliers_container is not None:
            self.suppliers_container.setParent(None)
            self.suppliers_container = None
        if hasattr(self, 'employees_container') and self.employees_container is not None:
            self.employees_container.setParent(None)
            self.employees_container = None
        if hasattr(self, 'settings_container') and self.settings_container is not None:
            self.settings_container.setParent(None)
            self.settings_container = None
        if hasattr(self, 'dashboard_container') and self.dashboard_container is not None:
            self.dashboard_container.setParent(None)
            self.dashboard_container = None
        
    def _connect_signals(self):
        # Connect SignalBus signals
        signalBus.logout_completed.connect(self.on_logout_completed)
        signalBus.database_error.connect(self.show_db_error)
        
    def _create_interfaces(self):
        """Create and initialize all interface widgets"""
        # Create empty containers for each interface section
        self.dashboard_container = QWidget()
        self.dashboard_container.setObjectName("dashboardContainer")
        self.orders_container = QWidget()
        self.orders_container.setObjectName("ordersContainer")
        self.clients_container = QWidget()
        self.clients_container.setObjectName("clientsContainer")
        self.inventory_container = QWidget()
        self.inventory_container.setObjectName("inventoryContainer")
        self.providers_container = QWidget()
        self.providers_container.setObjectName("providersContainer")
        self.schedule_container = QWidget()
        self.schedule_container.setObjectName("scheduleContainer")
        self.downloads_container = QWidget()
        self.downloads_container.setObjectName("downloadsContainer")
        self.settings_container = QWidget()
        self.settings_container.setObjectName("settingsContainer")
        self.create_order_container = QWidget()
        self.create_order_container.setObjectName("createOrderContainer")
        
        # Create empty layouts for each container
        self.dashboard_container.setLayout(QVBoxLayout())
        self.orders_container.setLayout(QVBoxLayout())
        self.clients_container.setLayout(QVBoxLayout())
        self.inventory_container.setLayout(QVBoxLayout())
        self.providers_container.setLayout(QVBoxLayout())
        self.schedule_container.setLayout(QVBoxLayout())
        self.downloads_container.setLayout(QVBoxLayout())
        self.settings_container.setLayout(QVBoxLayout())
        self.create_order_container.setLayout(QVBoxLayout())
        
        # Add interfaces to their respective containers
        
        # Dashboard interface
        self.dashboard_interface = DashboardInterface(self.user_data)
        self.dashboard_container.layout().addWidget(self.dashboard_interface)
        
        # Create order interface
        self.create_order_interface = CreateOrderInterface(self.user_data)
        self.create_order_container.layout().addWidget(self.create_order_interface)
        
        # Orders interface
        self.orders_interface = OrdersInterface(self.user_data)
        self.orders_container.layout().addWidget(self.orders_interface)
        
        # Profile interface
        self.profile_container = QWidget(self)
        self.profile_container.setObjectName("profileContainer")
        profile_layout = QVBoxLayout(self.profile_container)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        self.profile_interface = ProfileInterface(self.user_data, self.profile_container)
        profile_layout.addWidget(self.profile_interface)
        
        # Materials interface
        self.materials_container = QWidget(self)
        self.materials_container.setObjectName("materialsContainer")
        materials_layout = QVBoxLayout(self.materials_container)
        materials_layout.setContentsMargins(0, 0, 0, 0)
        self.materials_interface = MaterialsInterface(self.user_data, self.materials_container)
        materials_layout.addWidget(self.materials_interface)
        
        # Suppliers interface
        self.suppliers_container = QWidget(self)
        self.suppliers_container.setObjectName("suppliersContainer")
        suppliers_layout = QVBoxLayout(self.suppliers_container)
        suppliers_layout.setContentsMargins(0, 0, 0, 0)
        self.suppliers_interface = SuppliersInterface(self.user_data, self.suppliers_container)
        suppliers_layout.addWidget(self.suppliers_interface)
        
        # Settings interface
        self.settings_interface = SettingsInterface(self.settings_container) # SettingsInterface might not take user_data
        self.settings_container.layout().addWidget(self.settings_interface)
        
        # Add director-only interface if applicable
        self.employees_interface = None # Ensure it exists
        self.employees_container = None
        if self.user_data.get('position') == "Director":
            self.employees_container = QWidget(self)
            self.employees_container.setObjectName("employeesContainer")
            employees_layout = QVBoxLayout(self.employees_container)
            employees_layout.setContentsMargins(0, 0, 0, 0)
            self.employees_interface = EmployeesInterface(self.user_data, self.employees_container)
            employees_layout.addWidget(self.employees_interface)
        
    def _setup_navigation(self):
        # Настройка бокового меню
        self.navigationInterface.setFixedWidth(220)
        self.navigationInterface.setExpandWidth(260)
        self.navigationInterface.setReturnButtonVisible(False)
        
        # Add navigation items using addSubInterface
        self.addSubInterface(
            self.profile_container,
            icon=FluentIcon.PEOPLE,
            text="Профиль",
            position=NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.create_order_container,
            icon=FluentIcon.ADD,
            text="Создание заказа",
            position=NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.orders_container,
            icon=FluentIcon.DOCUMENT,
            text="Список заказов",
            position=NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.materials_container,
            icon=FluentIcon.BOOK_SHELF,
            text="Материалы",
            position=NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.suppliers_container,
            icon=FluentIcon.DOCUMENT,
            text="Поставщики",
            position=NavigationItemPosition.TOP
        )
        
        # Director-only item
        if self.user_data.get('position') == "Director" and self.employees_container:
            self.addSubInterface(
                self.employees_container,
                icon=FluentIcon.PEOPLE,
                text="Сотрудники",
                position=NavigationItemPosition.TOP
            )
        
        self.navigationInterface.addSeparator()
        
        # Add settings interface
        self.addSubInterface(
            self.settings_container,
            icon=FluentIcon.SETTING,
            text="Настройки",
            position=NavigationItemPosition.BOTTOM
        )
        
        # Set default interface
        self.navigationInterface.setCurrentItem(self.profile_container.objectName())
    
    def _show_welcome_message(self):
        """Показывает приветственное сообщение после входа в систему"""
        user_name = self.user_data.get('first', '')
        
        if user_name:
            InfoBar.success(
                title=f"Добро пожаловать, {user_name}!",
                content=f"Вы вошли как {self.user_data.get('position', 'сотрудник')}",
                orient=Qt.Orientation.Vertical,
                isClosable=True,
                duration=4000,
                parent=self
            )
            
    def closeEvent(self, event):
        """Переопределяем обработчик закрытия окна"""
        # Вызываем очистку ресурсов перед закрытием
        self._cleanup_resources()
        # Продолжаем стандартный процесс закрытия
        super().closeEvent(event)
        
    @pyqtSlot()
    def on_logout_completed(self):
        # Close worker window
        self.close()
        
    @pyqtSlot(str)
    def show_db_error(self, message):
        # Show database error
        InfoBar.error(
            title="Ошибка базы данных",
            content=message,
            parent=self,
            duration=5000
        )
        
    def _center_window(self):
        """Центрирует окно на экране"""
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
    def _onCurrentInterfaceChanged(self, widget):
        """Override to handle NoneType case"""
        if widget is None:
            return
            
        try:
            # Only try to set the current item if the widget has an objectName
            if hasattr(widget, 'objectName') and widget.objectName():
                self.navigationInterface.setCurrentItem(widget.objectName())
        except AttributeError:
            # Silently ignore attribute errors
            pass 