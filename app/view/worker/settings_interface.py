from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QColorDialog, QSizePolicy
from PyQt6.QtGui import QFont

from qfluentwidgets import (
    ScrollArea, PushButton, PrimaryPushButton, 
    InfoBar, SubtitleLabel, ComboBox, 
    CardWidget, FluentIcon, SimpleCardWidget, BodyLabel,
    MessageBox, isDarkTheme, setTheme, Theme,
    setThemeColor, InfoBarPosition, TitleLabel
)

from ...common.signal_bus import signalBus
from ...common.db.controller import AuthController
from ...common.config import config


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
            
            /* Card styles for dark theme */
            .QDarkTheme CardWidget {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
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

        # Категория: Аккаунт (будет переименована или интегрирована)
        self._add_account_section() # Placeholder for now

        # Категория: О приложении
        self._add_about_section() # Placeholder for now

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
        title_icon = QLabel() # Will be styled or replaced if needed
        title_icon.setPixmap(FluentIcon.PALETTE.icon().pixmap(24, 24)) # Using PALETTE like client
        title_label = SubtitleLabel("Персонализация")
        title_label.setFont(QFont("Segoe UI", 14, weight=QFont.Weight.Medium))

        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch(1)
        personalization_layout.addLayout(title_layout)

        # Theme selector
        theme_layout = QHBoxLayout()
        theme_label = BodyLabel("Тема приложения:") # Changed from QLabel
        theme_label.setMinimumWidth(150)

        self.theme_combo = ComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная", "Системная"]) # Matched client options
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed) # Connected

        # Set current theme
        if isDarkTheme():
            self.theme_combo.setCurrentText("Тёмная")
        else:
            self.theme_combo.setCurrentText("Светлая")

        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo, 1)
        personalization_layout.addLayout(theme_layout)
        # Removed apply_theme_button

        # Color theme selector
        color_layout = QHBoxLayout()
        color_label = BodyLabel("Цветовая схема:") # Changed from QLabel
        color_label.setMinimumWidth(150)

        self.color_button = PushButton("Выбрать цвет")
        self.color_button.setIcon(FluentIcon.PALETTE)
        self.color_button.clicked.connect(self._on_color_button_clicked) # Changed connection

        self.color_preview = QWidget() # Changed from ColorButton
        self.color_preview.setFixedSize(24, 24)
        # Initial color preview, can be set from config or default
        current_color = config.get("themeColor") # Get color without default
        if current_color is None: # Check if color was not found
            current_color = "#0078d4" # Apply default if not found
        self.color_preview.setStyleSheet(f"background-color: {current_color}; border-radius: 4px;")

        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(self.color_preview)
        color_layout.addStretch(1)
        personalization_layout.addLayout(color_layout)
        # Removed predefined colors section

        self.scroll_layout.addWidget(personalization_card)

    def _add_account_section(self):
        """Добавляет секцию управления аккаунтом"""
        account_card = CardWidget(self.scroll_widget)
        account_layout = QVBoxLayout(account_card)
        account_layout.setContentsMargins(20, 20, 20, 20)
        account_layout.setSpacing(15)

        # Add title with icon
        title_layout = QHBoxLayout()
        title_icon = QLabel() # Will be styled or replaced if needed
        title_icon.setPixmap(FluentIcon.PEOPLE.icon().pixmap(24, 24))
        account_title = SubtitleLabel("Аккаунт")
        account_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))

        title_layout.addWidget(title_icon)
        title_layout.addWidget(account_title)
        title_layout.addStretch(1)
        account_layout.addLayout(title_layout)

        # Logout button
        logout_layout = QHBoxLayout()
        logout_label = BodyLabel("Выход из аккаунта:") # Changed from QLabel
        # logout_label.setMinimumWidth(150) # Removed minimum width to allow natural sizing

        self.logout_button = PrimaryPushButton("Выйти из аккаунта")
        self.logout_button.setIcon(FluentIcon.RETURN)
        self.logout_button.clicked.connect(self.logout) # Existing logout method

        logout_layout.addWidget(logout_label)
        # logout_layout.addStretch(1) # Stretch before button can make it too far
        logout_layout.addWidget(self.logout_button)
        logout_layout.addStretch(1) # Stretch after button

        account_layout.addLayout(logout_layout)
        self.scroll_layout.addWidget(account_card)

    def _add_about_section(self):
        """Добавляет информацию о приложении (футер)"""
        about_card = SimpleCardWidget(self.scroll_widget) # Using SimpleCardWidget like client
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
        # Making separator color dynamic with theme
        line_color = "#CCCCCC" if not isDarkTheme() else "#555555" # Basic dynamic color
        line.setStyleSheet(f"background-color: {line_color};")
        line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        about_layout.addWidget(line)

        # Copyright
        copyright_label = BodyLabel("© 2025 Команда разработки Terra. Все права защищены.")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(copyright_label)

        self.scroll_layout.addWidget(about_card)

    def _on_theme_changed(self, index):
        """Изменяет тему приложения при выборе в ComboBox"""
        theme_text = self.theme_combo.itemText(index)

        if theme_text == "Светлая":
            QTimer.singleShot(0, lambda: setTheme(Theme.LIGHT))
        elif theme_text == "Тёмная":
            QTimer.singleShot(0, lambda: setTheme(Theme.DARK))
        else:  # System
            QTimer.singleShot(0, lambda: setTheme(Theme.LIGHT)) # Was Theme.AUTO

        try:
            config.set("themeMode", theme_text) # Changed config.themeMode to "themeMode"
        except Exception as e:
            print(f"Error saving theme to config: {e}") # Or use a logger

        InfoBar.success(
            title="Тема изменена",
            content=f"Установлена тема: {theme_text}",
            parent=self,
            duration=3000,
            position=InfoBarPosition.TOP_RIGHT
        )

    def _on_color_button_clicked(self):
        """Открывает диалог выбора цвета и применяет его"""
        try:
            # Using PyQt6.QtWidgets.QColorDialog directly
            dialog = QColorDialog(self) # Ensure dialog is parented
            color = dialog.getColor()

            if color.isValid():
                color_hex = color.name()
                self.color_preview.setStyleSheet(f"background-color: {color_hex}; border-radius: 4px;")
                setThemeColor(color_hex)

                try:
                    config.set("themeColor", color_hex) # Changed config.themeColor to "themeColor"
                except Exception as e:
                    print(f"Error saving color to config: {e}") # Or use a logger

                InfoBar.success(
                    title="Цвет изменен",
                    content=f"Установлен новый основной цвет: {color_hex}",
                    parent=self,
                    duration=3000,
                    position=InfoBarPosition.TOP_RIGHT
                )
        except Exception as e:
            InfoBar.error(
                title="Ошибка",
                content=f"Не удалось открыть диалог выбора цвета: {str(e)}",
                parent=self,
                duration=3000,
                position=InfoBarPosition.TOP_RIGHT # Added position
            )

    def logout(self):
        # Show confirmation dialog using proper MessageBox parameters
        message_box = MessageBox(
            title="Выход из аккаунта",
            content="Вы уверены, что хотите выйти из аккаунта?",
            parent=self.window()
        )
        message_box.yesButton.setText("Да")
        
        if message_box.exec():  # Returns True if Yes was clicked
            # Call logout method
            self.auth_controller.logout()
            signalBus.logout_completed.emit()
            # Main window will handle the rest 