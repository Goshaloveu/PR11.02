from PyQt6.QtCore import (
    Qt, QDate, pyqtSlot, QObject, QEvent, QThread, pyqtSignal, QSize
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout, 
    QGridLayout, QSizePolicy, QSpacerItem, QDialog
)
from PyQt6.QtGui import QFont, QIcon, QPixmap

from qfluentwidgets import (
    ScrollArea, PushButton, PrimaryPushButton, 
    InfoBar, SubtitleLabel, BodyLabel, CheckBox,
    CardWidget, FluentIcon, ComboBox, Dialog,
    TableWidget, StrongBodyLabel, ExpandLayout,
    SearchLineEdit, TitleLabel, InfoBarPosition,
    ToolTipFilter, ToolTipPosition, setTheme, Theme
)
from qfluentwidgets.components.date_time import FastCalendarPicker

from ...common.db.models_pydantic import OrderStatus
from ...common.db.controller import OrderController
from ...common.signal_bus import signalBus
from datetime import datetime, timedelta, date
import os
import tempfile


class OrdersInterface(ScrollArea):
    def __init__(self, user_data, parent=None):
        super().__init__(parent=parent)
        self.user_data = user_data
        self.order_controller = OrderController()
        
        # Установка objectName для интерфейса
        self.setObjectName("ordersInterface")
        
        # Create widget and layout
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(20)
        self.scroll_layout.setContentsMargins(30, 30, 30, 30)
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)
        
        # Create orders_layout early to avoid errors in load_orders
        self.orders_container = QWidget()
        self.orders_layout = QVBoxLayout(self.orders_container)
        self.orders_layout.setSpacing(15)
        self.orders_layout.setContentsMargins(5, 5, 5, 5)
        
        # Set modern fonts as class variables
        self.main_font = QFont("Inter", 10)
        self.header_font = QFont("Inter", 16, weight=QFont.Weight.DemiBold)
        self.section_font = QFont("Inter", 14, weight=QFont.Weight.Medium)
        self.setFont(self.main_font)
        
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
            #ordersInterface {
                background-color: transparent;
            }
            
            /* Card styles for dark theme */
            .QDarkTheme CardWidget {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
            }
            
            .QDarkTheme PushButton {
                background-color: #3D3D3D;
                border: 1px solid #4D4D4D;
                color: #FFFFFF;
            }
            
            .QDarkTheme PushButton:hover {
                background-color: #4D4D4D;
            }
        """)
        
        # Set up UI
        self._setup_ui()
        
        # Load orders
        self.load_orders()
        
    def _setup_ui(self):
        # Title
        title_label = TitleLabel("Мои заказы")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_layout.addWidget(title_label)
        
        # Description
        desc_label = BodyLabel("Здесь вы можете просматривать историю ваших заказов и их статусы")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_layout.addWidget(desc_label)
        
        # Set up a grid layout for better organization of filters and orders
        main_grid = QGridLayout()
        main_grid.setColumnStretch(0, 1)  # Make sure columns expand properly
        main_grid.setColumnStretch(1, 2)  # Orders column takes more space
        main_grid.setHorizontalSpacing(20)
        
        # Filters Card - Now in left column
        filter_card = CardWidget(self.scroll_widget)
        filter_layout = QVBoxLayout(filter_card)
        filter_layout.setContentsMargins(20, 20, 20, 20)
        filter_layout.setSpacing(15)
        
        # Filter header with icon
        filter_header = QHBoxLayout()
        filter_icon = QLabel()
        filter_icon.setPixmap(FluentIcon.FILTER.icon().pixmap(24, 24))
        filter_subtitle = StrongBodyLabel("Фильтры")
        filter_subtitle.setFont(self.header_font)
        
        filter_header.addWidget(filter_icon)
        filter_header.addWidget(filter_subtitle)
        filter_header.addStretch(1)
        filter_layout.addLayout(filter_header)
        
        # Search field with improved styling
        search_layout = QHBoxLayout()
        search_icon = QLabel()
        search_icon.setPixmap(FluentIcon.SEARCH.icon().pixmap(18, 18))
        search_layout.addWidget(search_icon)
        
        self.search_edit = SearchLineEdit(self)
        self.search_edit.setPlaceholderText("Поиск по ID заказа или имени сотрудника")
        self.search_edit.textChanged.connect(self.on_search_changed)
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMinimumHeight(36)
        search_layout.addWidget(self.search_edit)
        filter_layout.addLayout(search_layout)
        
        # Create filter grid layout for better organization
        filter_grid = QGridLayout()
        filter_grid.setColumnStretch(0, 1)
        filter_grid.setColumnStretch(1, 1)
        filter_grid.setColumnStretch(2, 1)
        filter_grid.setHorizontalSpacing(15)
        filter_grid.setVerticalSpacing(10)
        
        # Status filter
        status_label = StrongBodyLabel("Статус заказа:")
        self.status_combo = ComboBox()
        self.status_combo.addItems([
            "Все статусы", 
            OrderStatus.PROCESSING.value, 
            OrderStatus.IN_PROGRESS.value, 
            OrderStatus.COMPLETED.value
        ])
        self.status_combo.setCurrentIndex(0)
        self.status_combo.setToolTip("Фильтр по текущему статусу заказа")
        self.status_combo.setMinimumHeight(36)
        
        # Date filter section
        date_section_label = StrongBodyLabel("Фильтр по дате")
        date_section_label.setFont(QFont("Inter", 12, weight=QFont.Weight.Medium))
        
        # Use date filter checkbox with better placement
        self.use_date_filter = CheckBox("Использовать фильтр по дате")
        self.use_date_filter.setChecked(False)
        self.use_date_filter.stateChanged.connect(self.toggle_date_fields)
        
        # Date range filter with improved layout
        date_range_layout = QHBoxLayout()
        date_range_layout.setSpacing(15)
        
        # From date
        date_from_layout = QVBoxLayout()
        date_from_label = StrongBodyLabel("Дата с:")
        self.date_from = FastCalendarPicker(self)
        start_date = QDate.fromString((datetime.now().date() - timedelta(days=30)).strftime("%Y-%m-%d"), "yyyy-MM-dd")
        self.date_from.setDate(start_date)
        self.date_from.setToolTip("Начальная дата для фильтрации")
        
        date_from_layout.addWidget(date_from_label)
        date_from_layout.addWidget(self.date_from)
        date_range_layout.addLayout(date_from_layout, 1)
        
        # To date
        date_to_layout = QVBoxLayout()
        date_to_label = StrongBodyLabel("Дата по:")
        self.date_to = FastCalendarPicker(self)
        end_date = QDate.fromString(datetime.now().date().strftime("%Y-%m-%d"), "yyyy-MM-dd")
        self.date_to.setDate(end_date)
        self.date_to.setToolTip("Конечная дата для фильтрации")
        
        date_to_layout.addWidget(date_to_label)
        date_to_layout.addWidget(self.date_to)
        date_range_layout.addLayout(date_to_layout, 1)
        
        # Quick date filters with improved styling
        quick_date_layout = QVBoxLayout()
        quick_date_label = StrongBodyLabel("Быстрые фильтры:")
        
        quick_buttons_layout = QHBoxLayout()
        quick_buttons_layout.setSpacing(8)
        
        self.last_week_btn = PushButton("Неделя")
        self.last_week_btn.clicked.connect(lambda: self.set_quick_date_filter(7))
        self.last_week_btn.setToolTip("Показать заказы за последнюю неделю")
        self.last_week_btn.setIcon(FluentIcon.HISTORY)
        
        self.last_month_btn = PushButton("Месяц")
        self.last_month_btn.clicked.connect(lambda: self.set_quick_date_filter(30))
        self.last_month_btn.setToolTip("Показать заказы за последний месяц")
        self.last_month_btn.setIcon(FluentIcon.HISTORY)
        
        self.last_year_btn = PushButton("Год")
        self.last_year_btn.clicked.connect(lambda: self.set_quick_date_filter(365))
        self.last_year_btn.setToolTip("Показать заказы за последний год")
        self.last_year_btn.setIcon(FluentIcon.HISTORY)
        
        self.all_time_btn = PushButton("Все время")
        self.all_time_btn.clicked.connect(lambda: self.set_quick_date_filter(0))
        self.all_time_btn.setToolTip("Показать все заказы без ограничения по дате")
        self.all_time_btn.setIcon(FluentIcon.ALBUM)
        
        quick_buttons_layout.addWidget(self.last_week_btn)
        quick_buttons_layout.addWidget(self.last_month_btn)
        quick_buttons_layout.addWidget(self.last_year_btn)
        quick_buttons_layout.addWidget(self.all_time_btn)
        quick_buttons_layout.addStretch(1)
        
        quick_date_layout.addWidget(quick_date_label)
        quick_date_layout.addLayout(quick_buttons_layout)
        
        # Add to filter grid with better organization
        filter_grid.addWidget(status_label, 0, 0)
        filter_grid.addWidget(self.status_combo, 1, 0)
        
        filter_grid.addWidget(date_section_label, 2, 0, 1, 3)
        filter_grid.addWidget(self.use_date_filter, 3, 0, 1, 3)
        
        # Add date range as a separate row spanning all columns
        filter_grid.addLayout(date_range_layout, 4, 0, 1, 3)
        
        # Add quick date filters spanning all columns
        filter_grid.addLayout(quick_date_layout, 5, 0, 1, 3)
        
        filter_layout.addLayout(filter_grid)
        
        # Apply filter button with improved styling
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        
        self.reset_filter_button = PushButton("Сбросить фильтры")
        self.reset_filter_button.setIcon(FluentIcon.CANCEL)
        self.reset_filter_button.clicked.connect(self.reset_filters)
        
        self.apply_filter_button = PrimaryPushButton("Применить фильтры")
        self.apply_filter_button.setIcon(FluentIcon.ACCEPT)
        self.apply_filter_button.clicked.connect(self.load_orders)
        
        buttons_layout.addWidget(self.reset_filter_button)
        buttons_layout.addWidget(self.apply_filter_button)
        filter_layout.addLayout(buttons_layout)
        
        # Add filter card to the left column of the grid
        main_grid.addWidget(filter_card, 0, 0)
        
        # Initial state of date fields based on checkbox
        self.toggle_date_fields()
        
        # Orders Container - Make it take full available space in right column
        orders_card = CardWidget(self.scroll_widget)
        orders_layout = QVBoxLayout(orders_card)
        orders_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add just the order count label without the title
        orders_header = QHBoxLayout()
        orders_header.addStretch(1)
        
        # Order count label
        self.order_count_label = BodyLabel("Найдено заказов: 0")
        orders_header.addWidget(self.order_count_label)
        
        orders_layout.addLayout(orders_header)
        
        # Sort buttons - Make them more prominent and improved UI
        sort_layout = QHBoxLayout()
        sort_layout.setSpacing(12)
        
        # Create a card for sort controls to make them stand out
        sort_card = CardWidget()
        sort_card_layout = QVBoxLayout(sort_card)
        sort_card_layout.setContentsMargins(15, 15, 15, 15)
        
        # Sort header with icon
        sort_header = QHBoxLayout()
        sort_icon = QLabel()
        sort_icon.setPixmap(FluentIcon.ARROW_DOWN.icon().pixmap(24, 24))
        sort_title = StrongBodyLabel("Сортировка")
        sort_title.setFont(self.section_font)
        
        sort_header.addWidget(sort_icon)
        sort_header.addWidget(sort_title)
        sort_header.addStretch(1)
        sort_card_layout.addLayout(sort_header)
        
        # Sort controls
        sort_controls = QHBoxLayout()
        
        sort_by_label = StrongBodyLabel("Сортировать по:")
        sort_by_label.setFont(QFont("Inter", 11))
        sort_controls.addWidget(sort_by_label)
        
        # Date sort button with improved styling
        self.date_sort_btn = PushButton("Дате")
        self.date_sort_btn.setCheckable(True)
        self.date_sort_btn.setChecked(True)
        self.date_sort_btn.setIcon(FluentIcon.CALENDAR)
        self.date_sort_btn.clicked.connect(lambda: self.change_sort_mode('date'))
        self.date_sort_btn.setToolTip("Сортировать по дате создания заказа")
        sort_controls.addWidget(self.date_sort_btn)
        
        # Status sort button with improved styling
        self.status_sort_btn = PushButton("Статусу")
        self.status_sort_btn.setCheckable(True)
        self.status_sort_btn.setIcon(FluentIcon.TAG)
        self.status_sort_btn.clicked.connect(lambda: self.change_sort_mode('status'))
        self.status_sort_btn.setToolTip("Сортировать по статусу заказа")
        sort_controls.addWidget(self.status_sort_btn)
        
        # Sort direction button with improved icon and tooltip
        self.sort_dir_btn = PushButton()
        self.sort_dir_btn.setFixedWidth(40)
        self.sort_dir_btn.clicked.connect(self.toggle_sort_direction)
        self.sort_direction_asc = False  # Descending by default (new first)
        self.sort_dir_btn.setIcon(FluentIcon.UP)
        self.sort_dir_btn.setToolTip("Порядок сортировки (сейчас: по убыванию)")
        sort_controls.addWidget(self.sort_dir_btn)
        
        sort_controls.addStretch(1)
        sort_card_layout.addLayout(sort_controls)
        
        # Add the sort card to the layout
        orders_layout.addWidget(sort_card)
        orders_layout.addSpacing(10)
        
        # Add the container directly to the orders layout
        orders_layout.addWidget(self.orders_container, 1)  # 1 is the stretch factor
        
        # Add orders card to the right column of the grid
        main_grid.addWidget(orders_card, 0, 1)
        
        # Add the grid layout to the main scroll layout
        self.scroll_layout.addLayout(main_grid)
        
        # Add stretch to push everything to the top
        self.scroll_layout.addStretch(1)
        
    def toggle_date_fields(self):
        """Включает или отключает поля выбора дат в зависимости от состояния чекбокса"""
        enabled = self.use_date_filter.isChecked()
        self.date_from.setEnabled(enabled)
        self.date_to.setEnabled(enabled)
        self.last_week_btn.setEnabled(enabled)
        self.last_month_btn.setEnabled(enabled)
        self.last_year_btn.setEnabled(enabled)
        self.all_time_btn.setEnabled(enabled)
        
        # Only load orders if not during initial setup
        # We can check if the UI setup is complete by checking if we're visible
        if self.isVisible():
            self.load_orders()
    
    def set_quick_date_filter(self, days):
        """Устанавливает быстрый фильтр по дате"""
        today = datetime.now().date()
        if days > 0:
            start_date = today - timedelta(days=days)
            self.date_from.setDate(QDate.fromString(start_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
            self.date_to.setDate(QDate.fromString(today.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
            self.use_date_filter.setChecked(True)
        else:
            # "All time" option
            self.use_date_filter.setChecked(False)
        
        # Сброс стилей всех кнопок, сохраняя иконки
        for btn in [self.last_week_btn, self.last_month_btn, self.last_year_btn, self.all_time_btn]:
            btn.setStyleSheet("")
            
        # Выделяем нажатую кнопку с сохранением позиции иконки
        sender = self.sender()
        if sender:
            # Используем стиль, который учитывает положение иконки
            sender.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    padding-left: 5px;
                    padding-right: 5px;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #1082d9;
                }
            """)
            
        # Apply filters immediately
        self.load_orders()
    
    def reset_filters(self):
        """Сбрасывает все фильтры в исходное состояние"""
        self.status_combo.setCurrentIndex(0)
        self.use_date_filter.setChecked(False)
        
        # Reset dates with proper QDate conversion
        start_date = QDate.fromString((datetime.now().date() - timedelta(days=30)).strftime("%Y-%m-%d"), "yyyy-MM-dd")
        self.date_from.setDate(start_date)
        
        end_date = QDate.fromString(datetime.now().date().strftime("%Y-%m-%d"), "yyyy-MM-dd")
        self.date_to.setDate(end_date)
        
        self.search_edit.clear()
        
        # Reload orders with default filters
        self.load_orders()
        
        # Show notification
        InfoBar.success(
            title="Фильтры сброшены",
            content="Отображены все заказы",
            parent=self,
            duration=3000,
            position=InfoBarPosition.TOP
        )
    
    def on_search_changed(self):
        """Обрабатывает изменение текста поиска"""
        # Если задержка короткая, можно применять фильтр сразу
        self.load_orders()
        
    def change_sort_mode(self, mode):
        """Изменяет режим сортировки и обновляет внешний вид кнопок"""
        if mode == 'date':
            self.date_sort_btn.setChecked(True)
            self.status_sort_btn.setChecked(False)
        else:  # status
            self.date_sort_btn.setChecked(False)
            self.status_sort_btn.setChecked(True)
            
        # Reload orders with new sorting
        self.load_orders()
    
    def toggle_sort_direction(self):
        """Переключает направление сортировки"""
        self.sort_direction_asc = not self.sort_direction_asc
        if self.sort_direction_asc:
            self.sort_dir_btn.setIcon(FluentIcon.DOWN)
            self.sort_dir_btn.setToolTip("Порядок сортировки (сейчас: по возрастанию)")
        else:
            self.sort_dir_btn.setIcon(FluentIcon.UP)
            self.sort_dir_btn.setToolTip("Порядок сортировки (сейчас: по убыванию)")
        
        # Reload orders with new sort direction
        self.load_orders()
    
    def load_orders(self):
        """Загружает заказы с учетом фильтров"""
        # Safety check - make sure orders_layout is initialized
        if not hasattr(self, 'orders_layout'):
            print("Warning: orders_layout not initialized yet, skipping load_orders")
            return
            
        # Get filter values
        status_filter = self.status_combo.currentText()
        search_query = self.search_edit.text().strip().lower()
        
        # Get date range if enabled
        date_from = None
        date_to = None
        if self.use_date_filter.isChecked():
            # Convert QDate back to Python date for comparison
            date_from = self.date_from.getDate().toPyDate()
            date_to = self.date_to.getDate().toPyDate()
        
        # Clear existing orders
        for i in reversed(range(self.orders_layout.count())): 
            item = self.orders_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        
        try:
            # Get all orders for this client
            client_id = self.user_data.get('id')
            
            # Check if client_id exists
            if not client_id:
                # Show message if client ID is missing
                error_label = BodyLabel("Ошибка: ID клиента не найден. Пожалуйста, войдите в систему заново.")
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.orders_layout.addWidget(error_label)
                self.order_count_label.setText("Ошибка загрузки")
                
                # Log error
                InfoBar.error(
                    title="Ошибка загрузки",
                    content="ID клиента не найден",
                    parent=self,
                    duration=5000
                )
                return
            
            orders = self.order_controller.get_orders_by_client(client_id)
            
            if not orders:
                # Show message if no orders found
                no_orders_label = BodyLabel("У вас пока нет заказов")
                no_orders_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.orders_layout.addWidget(no_orders_label)
                self.order_count_label.setText("Найдено заказов: 0")
                return
            
            # Apply filters
            filtered_orders = []
            for order in orders:
                # Status filter
                if status_filter != "Все статусы" and order.status != status_filter:
                    continue
                
                # Search filter
                order_worker_name = ""
                if order.worker:  # Check if worker exists
                    order_worker_name = f"{order.worker.first} {order.worker.last}"
                
                if search_query and search_query not in str(order.id).lower() and search_query not in order_worker_name.lower():
                    continue
                
                # Date filter
                if self.use_date_filter.isChecked() and date_from and date_to:
                    order_date = order.date.date()  # Convert datetime to date for comparison
                    if not (date_from <= order_date <= date_to):
                        continue
                
                filtered_orders.append(order)
            
            # Sort orders
            if self.status_sort_btn.isChecked():
                # Sort by status
                status_priority = {
                    OrderStatus.IN_PROGRESS.value: 1,
                    OrderStatus.PROCESSING.value: 2,
                    OrderStatus.COMPLETED.value: 3
                }
                filtered_orders.sort(key=lambda x: status_priority.get(x.status, 999))
            else:
                # Sort by date
                filtered_orders.sort(key=lambda x: x.date, reverse=not self.sort_direction_asc)
            
            # Update order count
            self.order_count_label.setText(f"Найдено заказов: {len(filtered_orders)}")
            
            # Create order cards
            if filtered_orders:
                for order in filtered_orders:
                    card = self._create_order_card(order)
                    self.orders_layout.addWidget(card)
            else:
                # No orders after filtering
                no_orders_label = BodyLabel("Заказы не найдены. Попробуйте изменить параметры фильтра.")
                no_orders_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.orders_layout.addWidget(no_orders_label)
            
        except Exception as e:
            # Show error message
            error_label = BodyLabel(f"Ошибка при загрузке заказов: {str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.orders_layout.addWidget(error_label)
            self.order_count_label.setText("Ошибка загрузки")
            
            # Log error
            InfoBar.error(
                title="Ошибка загрузки",
                content=str(e),
                parent=self,
                duration=5000
            )
    
    def _create_order_card(self, order):
        """Создает карточку заказа для отображения"""
        # Create card
        card = CardWidget()
        card.setObjectName(f"order_{order.id}")
        card.setStyleSheet("""
            CardWidget {
                border-radius: 8px;
            }
            CardWidget:hover {
                border: 1px solid #ddd;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)
        
        # Header with order ID and date
        header = QHBoxLayout()
        
        # Order ID with icon
        id_layout = QHBoxLayout()
        doc_icon = QLabel()
        doc_icon.setPixmap(FluentIcon.DOCUMENT.icon().pixmap(18, 18))
        id_label = StrongBodyLabel(f"Заказ #{str(order.id)[:8]}")
        id_label.setFont(self.main_font)
        
        id_layout.addWidget(doc_icon)
        id_layout.addWidget(id_label)
        header.addLayout(id_layout)
        
        # Date info
        header.addStretch(1)
        
        date_label = QLabel(str(order.date).split(' ')[0])
        date_label.setStyleSheet("color: #777; font-size: 13px;")
        header.addWidget(date_label)
        
        layout.addLayout(header)
        
        # Status with color
        status = order.status
        status_layout = QHBoxLayout()
        
        status_label = QLabel("Статус:")
        status_label.setStyleSheet("color: #444; font-weight: 500;")
        
        status_value = QLabel(status)
        status_value.setStyleSheet("font-weight: bold; padding: 4px 8px; border-radius: 4px;")
        
        # Set color based on status
        if status == OrderStatus.PROCESSING.value:
            status_value.setStyleSheet("font-weight: bold; color: #B45F06; background: #FFF2CC; padding: 4px 8px; border-radius: 4px;")
        elif status == OrderStatus.IN_PROGRESS.value:
            status_value.setStyleSheet("font-weight: bold; color: #1155CC; background: #D0E0F3; padding: 4px 8px; border-radius: 4px;")
        elif status == OrderStatus.COMPLETED.value:
            status_value.setStyleSheet("font-weight: bold; color: #38761D; background: #D9EAD3; padding: 4px 8px; border-radius: 4px;")
            
        status_layout.addWidget(status_label)
        status_layout.addWidget(status_value)
        status_layout.addStretch(1)
        layout.addLayout(status_layout)
        
        # Employee assigned
        worker = order.worker
        worker_layout = QHBoxLayout()
        worker_label = QLabel("Сотрудник:")
        worker_label.setStyleSheet("color: #444; font-weight: 500;")
        
        if worker:
            worker_name = f"{worker.first} {worker.last}"
            worker_value = QLabel(worker_name)
        else:
            worker_value = QLabel("Не назначен")
        
        worker_layout.addWidget(worker_label)
        worker_layout.addWidget(worker_value)
        worker_layout.addStretch(1)
        layout.addLayout(worker_layout)
        
        # Actions
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        
        # View details button
        view_button = PushButton("Детали")
        view_button.setIcon(FluentIcon.SEARCH)
        view_button.setObjectName(f"view_{order.id}")
        view_button.clicked.connect(lambda: self.show_order_details(order.id))
        buttons_layout.addWidget(view_button)
        
        # Download button (only for completed orders)
        if order.status == OrderStatus.COMPLETED.value:
            download_button = PushButton("Скачать")
            download_button.setIcon(FluentIcon.DOWNLOAD)
            download_button.setObjectName(f"download_{order.id}")
            download_button.clicked.connect(lambda: self.download_order_statement(order.id))
            buttons_layout.addWidget(download_button)
        
        layout.addLayout(buttons_layout)
        
        # Add card to container
        return card
    
    def show_order_details(self, order_id):
        try:
            from ...common.db.database import SessionLocal
            db = SessionLocal()
            
            # Get order details
            order = self.order_controller.get_by_id(db, order_id)
            
            if order:
                # Show order details dialog
                details_dialog = OrderDetailsDialog(order, self)
                details_dialog.exec()
        except Exception as e:
            InfoBar.error(
                title="Ошибка загрузки деталей заказа",
                content=str(e),
                parent=self
            )
        finally:
            SessionLocal.remove()
            
    def download_order_statement(self, order_id):
        try:
            from ...common.db.database import SessionLocal
            db = SessionLocal()
            
            # Get order details
            order = self.order_controller.get_by_id(db, order_id)
            
            if order:
                # Generate PDF statement
                from ...common.utils.document_generator import generate_order_statement
                pdf_path = generate_order_statement(order)
                
                if pdf_path:
                    # Show success message with file path
                    InfoBar.success(
                        title="Документ создан",
                        content=f"Документ сохранен: {pdf_path}",
                        parent=self,
                        duration=5000,
                        position=InfoBarPosition.TOP
                    )
                    
                    # Open file in default PDF viewer
                    import subprocess
                    import platform
                    
                    try:
                        if platform.system() == 'Windows':
                            os.startfile(pdf_path)
                        elif platform.system() == 'Darwin':
                            subprocess.call(('open', pdf_path))
                        else:
                            subprocess.call(('xdg-open', pdf_path))
                    except Exception as e:
                        InfoBar.warning(
                            title="Не удалось открыть файл",
                            content=f"Файл сохранен, но не удалось открыть его автоматически: {e}",
                            parent=self
                        )
        except Exception as e:
            InfoBar.error(
                title="Ошибка создания документа",
                content=str(e),
                parent=self
            )
        finally:
            SessionLocal.remove()


class OrderDetailsDialog(QDialog):
    def __init__(self, order_data, parent=None):
        super().__init__(parent)
        self.order_data = order_data
        self.setWindowTitle("Детали заказа")
        self.resize(600, 500)
        
        # Set up UI
        self._setup_ui()
        
    def _setup_ui(self):
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Order info
        self.order_id_label = TitleLabel(f"Заказ №{self.order_data.id}")
        self.order_id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.order_id_label)
        
        # Status label with color
        status = self.order_data.status
        status_layout = QHBoxLayout()
        status_label = QLabel("Статус:")
        status_value = QLabel(status)
        status_value.setStyleSheet("font-weight: bold;")
        
        if status == OrderStatus.PROCESSING.value:
            status_value.setStyleSheet("font-weight: bold; color: #B45F06;")  # Orange
        elif status == OrderStatus.IN_PROGRESS.value:
            status_value.setStyleSheet("font-weight: bold; color: #1155CC;")  # Blue
        elif status == OrderStatus.COMPLETED.value:
            status_value.setStyleSheet("font-weight: bold; color: #38761D;")  # Green
            
        status_layout.addWidget(status_label)
        status_layout.addWidget(status_value)
        status_layout.addStretch(1)
        main_layout.addLayout(status_layout)
        
        # Create card for order details
        details_card = CardWidget(self)
        details_layout = QVBoxLayout(details_card)
        details_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create form layout for order info
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(10)
        
        # Order dates
        date_created = str(self.order_data.date)
        date_updated = "Не обновлялся"  # Since there's no update_date field in the Order model
        
        form_layout.addRow(StrongBodyLabel("Дата создания:"), QLabel(date_created))
        form_layout.addRow(StrongBodyLabel("Дата обновления:"), QLabel(date_updated))
        
        # Employee info
        worker = self.order_data.worker
        if worker:
            worker_name = f"{worker.first} {worker.last}"
            worker_phone = worker.phone or "Не указан"
            worker_email = worker.mail or "Не указан"
            
            form_layout.addRow(StrongBodyLabel("Сотрудник:"), QLabel(worker_name))
            form_layout.addRow(StrongBodyLabel("Телефон:"), QLabel(worker_phone))
            form_layout.addRow(StrongBodyLabel("Email:"), QLabel(worker_email))
        else:
            form_layout.addRow(StrongBodyLabel("Сотрудник:"), QLabel("Не назначен"))
            
        details_layout.addLayout(form_layout)
        
        main_layout.addWidget(details_card, 1)  # 1 - stretch factor
        
        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 10, 0, 0)
        
        # If order is completed, add download button
        if self.order_data.status == OrderStatus.COMPLETED.value:
            self.download_button = PushButton("Скачать документ")
            self.download_button.setIcon(FluentIcon.DOWNLOAD)
            self.download_button.clicked.connect(self.download_statement)
            actions_layout.addWidget(self.download_button)
            
        # Add spacing between buttons
        actions_layout.addStretch(1)
        
        self.close_button = PrimaryPushButton("Закрыть")
        self.close_button.clicked.connect(self.accept)
        actions_layout.addWidget(self.close_button)
        
        main_layout.addLayout(actions_layout)
    
    def download_statement(self):
        try:
            # Generate PDF statement
            from ...common.utils.document_generator import generate_order_statement
            pdf_path = generate_order_statement(self.order_data)
            
            if pdf_path:
                # Show success message with file path
                InfoBar.success(
                    title="Документ создан",
                    content=f"Документ сохранен: {pdf_path}",
                    parent=self,
                    duration=3000
                )
                
                # Open file in default PDF viewer
                import subprocess
                import platform
                
                try:
                    if platform.system() == 'Windows':
                        os.startfile(pdf_path)
                    elif platform.system() == 'Darwin':
                        subprocess.call(('open', pdf_path))
                    else:
                        subprocess.call(('xdg-open', pdf_path))
                except Exception as e:
                    InfoBar.warning(
                        title="Не удалось открыть файл",
                        content=f"Файл сохранен, но не удалось открыть его автоматически: {e}",
                        parent=self
                    )
        except Exception as e:
            InfoBar.error(
                title="Ошибка создания документа",
                content=str(e),
                parent=self
            ) 