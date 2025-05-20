from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import QEvent, QObject

from qfluentwidgets import (
    FluentWindow, NavigationInterface, NavigationItemPosition, 
    setTheme, Theme, InfoBar, MessageBox, InfoBarPosition,
    FluentIcon, PrimaryPushButton, setStyleSheet
)

from ...common.signal_bus import signalBus
from .profile_interface import ProfileInterface
from .orders_interface import OrdersInterface
from .settings_interface import SettingsInterface


class ClientWindow(FluentWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.setWindowTitle("Terra - Кабинет клиента")
        # self.resize(1100, 750) # Commented out fixed size

        # Adaptive sizing
        screen = QApplication.primaryScreen().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()

        # Define desired proportions and limits
        desired_width = int(screen_width * 0.8)
        desired_height = int(screen_height * 0.8)

        # Clamp to min/max sizes (same as WorkerWindow for consistency)
        min_w, min_h = 900, 650 # Minimum window size
        max_w, max_h = 1300, 900 # Maximum initial window size

        initial_width = max(min_w, min(desired_width, max_w))
        initial_height = max(min_h, min(desired_height, max_h))

        self.resize(initial_width, initial_height)
        self.setMinimumSize(min_w, min_h)
        
        # Устанавливаем лёгкую тему для приложения
        setTheme(Theme.LIGHT)
        
        # Исправление ошибки QBackingStore::endPaint() - уничтожаем QPainter перед закрытием окна
        self.destroyed.connect(self._cleanup_resources)
        
        # Create interfaces
        self._setup_interfaces()
        
        # Connect signals
        self._connect_signals()
        
        # Add items to navigation interface
        self._setup_navigation()
        
        # Центрируем окно на экране
        self._center_window()
        
        # Показываем приветствие
        self._show_welcome_message()
        
    def _cleanup_resources(self):
        """Метод для очистки ресурсов перед закрытием окна"""
        # Этот метод вызывается при уничтожении окна и решает проблему с QBackingStore::endPaint()
        # Принудительно освобождаем ресурсы интерфейсов
        if hasattr(self, 'profile_interface') and self.profile_interface is not None:
            self.profile_interface.setParent(None)
            self.profile_interface = None
        if hasattr(self, 'profile_container') and self.profile_container is not None:
            self.profile_container.setParent(None)
            self.profile_container = None
            
        if hasattr(self, 'orders_interface') and self.orders_interface is not None:
            self.orders_interface.setParent(None)
            self.orders_interface = None
        if hasattr(self, 'orders_container') and self.orders_container is not None:
            self.orders_container.setParent(None)
            self.orders_container = None
            
        if hasattr(self, 'settings_interface') and self.settings_interface is not None:
            self.settings_interface.setParent(None)
            self.settings_interface = None
        if hasattr(self, 'settings_container') and self.settings_container is not None:
            self.settings_container.setParent(None)
            self.settings_container = None
        
    def _connect_signals(self):
        # Connect SignalBus signals
        signalBus.logout_completed.connect(self.on_logout_completed)
        signalBus.database_error.connect(self.show_db_error)
        
    def _setup_interfaces(self):
        # Create interfaces using container widgets
        # Создаем контейнерные виджеты, которые будут содержать интерфейсы в логичном порядке
        # 1. Контейнер заказов (первый, т.к. это главная вкладка)
        self.orders_container = QWidget()
        self.orders_container.setObjectName("orders")
        orders_layout = QVBoxLayout()
        orders_layout.setContentsMargins(0, 0, 0, 0)
        self.orders_container.setLayout(orders_layout)
        self.orders_interface = OrdersInterface(self.user_data, self.orders_container)
        orders_layout.addWidget(self.orders_interface)
        
        # 2. Контейнер профиля
        self.profile_container = QWidget()
        self.profile_container.setObjectName("profile")
        profile_layout = QVBoxLayout()
        profile_layout.setContentsMargins(0, 0, 0, 0)
        self.profile_container.setLayout(profile_layout)
        self.profile_interface = ProfileInterface(self.user_data, self.profile_container)
        profile_layout.addWidget(self.profile_interface)
        
        # 3. Контейнер настроек
        self.settings_container = QWidget()
        self.settings_container.setObjectName("settings")
        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(0, 0, 0, 0)
        self.settings_container.setLayout(settings_layout)
        self.settings_interface = SettingsInterface(self.settings_container)
        settings_layout.addWidget(self.settings_interface)
    
    def _setup_navigation(self):
        # Настройка бокового меню
        self.navigationInterface.setFixedWidth(220)
        self.navigationInterface.setExpandWidth(260)
        self.navigationInterface.setReturnButtonVisible(False)
        
        # Add navigation items with improved icons
        self.addSubInterface(
            self.orders_container,
            icon=FluentIcon.DOCUMENT,
            text="Мои заказы",
            position=NavigationItemPosition.TOP
        )

        self.navigationInterface.addSeparator()

        self.addSubInterface(
            self.profile_container,
            icon=FluentIcon.PEOPLE,
            text="Личный профиль",
            position=NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.settings_container,
            icon=FluentIcon.SETTING,
            text="Настройки",
            position=NavigationItemPosition.BOTTOM
        )
        
        # Set default interface
        self.navigationInterface.setCurrentItem("orders")
        
    def _show_welcome_message(self):
        """Показывает приветственное сообщение после входа в систему"""
        user_name = self.user_data.get('first', '')
        
        if user_name:
            InfoBar.success(
                title=f"Добро пожаловать, {user_name}!",
                content="Вы успешно вошли в личный кабинет",
                orient=Qt.Orientation.Vertical,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
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
        # Close client window
        self.close()
        
    @pyqtSlot(str)
    def show_db_error(self, message):
        # Show database error
        InfoBar.error(
            title="Ошибка базы данных",
            content=message,
            position=InfoBarPosition.TOP,
            parent=self,
            duration=5000
        )
        
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

    def _center_window(self):
        """Центрирует окно на экране"""
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y) 