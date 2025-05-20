from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QFont, QColor

from qfluentwidgets import (
    ScrollArea, PushButton, PrimaryPushButton, 
    InfoBar, SubtitleLabel, ComboBox, 
    CardWidget, FluentIcon, TogglePushButton,
    MessageBox, isDarkTheme, setTheme, Theme,
    setThemeColor, TitleLabel, ColorDialog, BodyLabel,
    InfoBarPosition, SimpleCardWidget, SwitchButton
)

from ...common.db.controller import AuthController
from ...common.signal_bus import signalBus


class SettingsInterface(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.auth_controller = AuthController()
        
        # Установка objectName для интерфейса
        self.setObjectName("settingsInterface")
        
        # Create widget and layout
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(24)
        self.scroll_layout.setContentsMargins(30, 30, 30, 30)
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)
        
        # Fix dark mode scrollbar issues
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            /* For light theme */
            QScrollBar:vertical {
                border: none;
                background: #F0F0F0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #CCCCCC;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #BBBBBB;
            }
            
            /* For dark theme */
            .QDarkTheme QScrollBar:vertical {
                border: none;
                background: #333333;
                width: 10px;
                margin: 0px;
            }
            .QDarkTheme QScrollBar::handle:vertical {
                background: #666666;
                min-height: 20px;
                border-radius: 5px;
            }
            .QDarkTheme QScrollBar::handle:vertical:hover {
                background: #777777;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                height: 0px;
                background: none;
            }
            
            /* Widget background fix for dark theme */
            #settingsInterface {
                background-color: transparent;
            }
        """)
        
        # Set up UI
        self._setup_ui()
        
    def _setup_ui(self):
        # Title
        self.title_label = TitleLabel("Настройки")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_layout.addWidget(self.title_label)
        
        # Категория: Персонализация
        self._add_personalization_section()
        
        # Категория: Уведомления
        self._add_notification_section()
        
        # Категория: Система
        self._add_system_section()
        
        # Категория: О приложении
        self._add_about_section()
        
        # Add stretch to push cards to the top
        self.scroll_layout.addStretch(1)
    
    def _add_personalization_section(self):
        """Добавляет секцию с настройками персонализации"""
        # Create personalization card
        personalization_card = CardWidget(self.scroll_widget)
        personalization_layout = QVBoxLayout(personalization_card)
        personalization_layout.setContentsMargins(20, 20, 20, 20)
        personalization_layout.setSpacing(15)
        
        # Add title with icon
        title_layout = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(FluentIcon.PALETTE.icon().pixmap(24, 24))
        title_label = SubtitleLabel("Персонализация")
        title_label.setFont(QFont("Segoe UI", 14, weight=QFont.Weight.Medium))
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch(1)
        personalization_layout.addLayout(title_layout)
        
        # Theme selector
        theme_layout = QHBoxLayout()
        theme_label = BodyLabel("Тема приложения:")
        theme_label.setMinimumWidth(150)
        
        self.theme_combo = ComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная", "Системная (авто)"])
        self.theme_combo.setCurrentIndex(0)  # По умолчанию - светлая тема
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo, 1)
        personalization_layout.addLayout(theme_layout)
        
        # Color theme selector
        color_layout = QHBoxLayout()
        color_label = BodyLabel("Цветовая схема:")
        color_label.setMinimumWidth(150)
        
        self.color_button = PushButton("Выбрать цвет")
        self.color_button.setIcon(FluentIcon.PALETTE)
        self.color_button.clicked.connect(self._on_color_button_clicked)
        
        self.color_preview = QWidget()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setStyleSheet("background-color: #0078d4; border-radius: 4px;")
        
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(self.color_preview)
        color_layout.addStretch(1)
        personalization_layout.addLayout(color_layout)
        
        self.scroll_layout.addWidget(personalization_card)
    
    def _add_notification_section(self):
        """Добавляет секцию с настройками уведомлений"""
        # Create notifications card
        notifications_card = CardWidget(self.scroll_widget)
        notifications_layout = QVBoxLayout(notifications_card)
        notifications_layout.setContentsMargins(20, 20, 20, 20)
        notifications_layout.setSpacing(15)
        
        # Add title with icon
        title_layout = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(FluentIcon.MAIL.icon().pixmap(24, 24))
        title_label = SubtitleLabel("Уведомления")
        title_label.setFont(QFont("Segoe UI", 14, weight=QFont.Weight.Medium))
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch(1)
        notifications_layout.addLayout(title_layout)
        
        # Email notifications
        email_layout = QHBoxLayout()
        email_label = BodyLabel("Получать уведомления по электронной почте:")
        
        self.email_notifications_switch = SwitchButton()
        
        email_layout.addWidget(email_label, 1)
        email_layout.addWidget(self.email_notifications_switch)
        notifications_layout.addLayout(email_layout)
        
        # Status change notifications
        status_layout = QHBoxLayout()
        status_label = BodyLabel("Уведомлять об изменении статуса заказа:")
        
        self.status_notifications_switch = SwitchButton()
        self.status_notifications_switch.setChecked(True)
        
        status_layout.addWidget(status_label, 1)
        status_layout.addWidget(self.status_notifications_switch)
        notifications_layout.addLayout(status_layout)
        
        # New features notifications
        features_layout = QHBoxLayout()
        features_label = BodyLabel("Уведомлять о новых функциях:")
        
        self.features_notifications_switch = SwitchButton()
        self.features_notifications_switch.setChecked(True)
        
        features_layout.addWidget(features_label, 1)
        features_layout.addWidget(self.features_notifications_switch)
        notifications_layout.addLayout(features_layout)
        
        self.scroll_layout.addWidget(notifications_card)
    
    def _add_system_section(self):
        """Добавляет системную секцию с кнопкой выхода и других системных функций"""
        # Create system card
        system_card = CardWidget(self.scroll_widget)
        system_layout = QVBoxLayout(system_card)
        system_layout.setContentsMargins(20, 20, 20, 20)
        system_layout.setSpacing(15)
        
        # Add title with icon
        title_layout = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(FluentIcon.SETTING.icon().pixmap(24, 24))
        title_label = SubtitleLabel("Система")
        title_label.setFont(QFont("Segoe UI", 14, weight=QFont.Weight.Medium))
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch(1)
        system_layout.addLayout(title_layout)
        
        # Cache control
        cache_layout = QHBoxLayout()
        cache_label = BodyLabel("Управление кешем:")
        
        self.clear_cache_button = PushButton("Очистить кеш")
        self.clear_cache_button.setIcon(FluentIcon.DELETE)
        self.clear_cache_button.clicked.connect(self._on_clear_cache_clicked)
        
        cache_layout.addWidget(cache_label)
        cache_layout.addWidget(self.clear_cache_button)
        cache_layout.addStretch(1)
        system_layout.addLayout(cache_layout)
        
        # Logout button
        logout_layout = QHBoxLayout()
        logout_label = BodyLabel("Выход из аккаунта:")
        
        self.logout_button = PrimaryPushButton("Выйти")
        self.logout_button.setIcon(FluentIcon.RETURN)
        self.logout_button.clicked.connect(self._on_logout_clicked)
        
        logout_layout.addWidget(logout_label)
        logout_layout.addWidget(self.logout_button)
        logout_layout.addStretch(1)
        system_layout.addLayout(logout_layout)
        
        self.scroll_layout.addWidget(system_card)
    
    def _add_about_section(self):
        """Добавляет информацию о приложении"""
        # Create about card
        about_card = SimpleCardWidget(self.scroll_widget)
        about_layout = QVBoxLayout(about_card)
        about_layout.setContentsMargins(20, 20, 20, 20)
        about_layout.setSpacing(10)
        
        # App name and version
        app_name_label = SubtitleLabel("Приложение Terra")
        app_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        version_label = BodyLabel("Версия 1.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        about_layout.addWidget(app_name_label)
        about_layout.addWidget(version_label)
        
        # Separator
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #CCCCCC;")
        line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        about_layout.addWidget(line)
        
        # Copyright
        copyright_label = BodyLabel("© 2025 Команда разработки Terra. Все права защищены.")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(copyright_label)
        
        self.scroll_layout.addWidget(about_card)
    
    def _on_theme_changed(self, index):
        """Изменяет тему приложения"""
        if index == 0:  # Light
            setTheme(Theme.LIGHT)
            InfoBar.success(
                title="Тема изменена",
                content="Установлена светлая тема",
                parent=self,
                duration=3000,
                position=InfoBarPosition.TOP_RIGHT
            )
        elif index == 1:  # Dark
            setTheme(Theme.DARK)
            InfoBar.success(
                title="Тема изменена",
                content="Установлена тёмная тема",
                parent=self,
                duration=3000,
                position=InfoBarPosition.TOP_RIGHT
            )
        else:  # Auto
            # Определяем системную тему (в данном случае просто устанавливаем светлую)
            setTheme(Theme.LIGHT)
            InfoBar.success(
                title="Тема изменена",
                content="Установлена системная тема",
                parent=self,
                duration=3000,
                position=InfoBarPosition.TOP_RIGHT
            )
    
    def _on_color_button_clicked(self):
        """Открывает диалог выбора цвета"""
        try:
            # Use QColorDialog instead of ColorDialog
            from PyQt6.QtWidgets import QColorDialog
            color = QColorDialog.getColor()
            
            if color.isValid():
                self.color_preview.setStyleSheet(f"background-color: {color.name()}; border-radius: 4px;")
                
                # Apply the new theme color
                setThemeColor(color.name())
                
                InfoBar.success(
                    title="Цвет изменен",
                    content=f"Установлен новый основной цвет: {color.name()}",
                    parent=self,
                    duration=3000,
                    position=InfoBarPosition.TOP_RIGHT
                )
        except Exception as e:
            InfoBar.error(
                title="Ошибка",
                content=f"Не удалось открыть диалог выбора цвета: {str(e)}",
                parent=self,
                duration=3000
            )
    
    def _on_clear_cache_clicked(self):
        """Имитирует очистку кеша"""
        # Здесь должна быть реальная очистка кеша приложения
        InfoBar.success(
            title="Кеш очищен",
            content="Кеш приложения успешно очищен",
            parent=self,
            duration=3000,
            position=InfoBarPosition.TOP_RIGHT
        )
    
    def _on_logout_clicked(self):
        """Выход из аккаунта"""
        # Confirm logout
        box = MessageBox(
            title="Выход из аккаунта",
            content="Вы действительно хотите выйти из аккаунта?",
            parent=self.window()
        )
        
        box.yesButton.setText("Выйти")
        box.cancelButton.setText("Отмена")
        
        if box.exec():
            # Logout from account
            try:
                self.auth_controller.logout()
                signalBus.logout_completed.emit()
                
                # Show success message
                InfoBar.success(
                    title="Выход выполнен",
                    content="Вы успешно вышли из аккаунта",
                    parent=self.window(),
                    duration=3000,
                    position=InfoBarPosition.TOP_RIGHT
                )
            except Exception as e:
                # Show error message
                InfoBar.error(
                    title="Ошибка выхода",
                    content=str(e),
                    parent=self.window(),
                    duration=3000
                ) 