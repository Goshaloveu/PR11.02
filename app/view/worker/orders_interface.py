from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QDateEdit, QPushButton, QLineEdit, QDialog, QMessageBox,
    QSpinBox, QFormLayout, QScrollArea, QGroupBox, QListWidget,
    QSizePolicy
)

from qfluentwidgets import (
    FluentIcon, InfoBar, Dialog, ComboBox, 
    PushButton, TableWidget, LineEdit, SpinBox, 
    DateEdit, SearchLineEdit, MessageBox, IndeterminateProgressBar,
    StrongBodyLabel, BodyLabel, CaptionLabel, SubtitleLabel,
    CardWidget, PrimaryPushButton, TransparentToolButton,
    SwitchButton, ToolButton
)

from ...common.db.controller import OrderController, ClientController, WorkerController, MaterialController
from ...common.db.models_pydantic import OrderStatus, OrderUpdate, MaterialOnOrderCreate
from ...common.db.database import SessionLocal
from ...common.signal_bus import signalBus
import uuid
from datetime import datetime, timedelta
import fpdf
import os
import tempfile
import os.path

class OrdersInterface(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        
        # Initialize controllers
        self.order_controller = OrderController()
        self.client_controller = ClientController()
        self.worker_controller = WorkerController()
        
        # Initialize filters
        self.filters = {
            "status": None,
            "client_id": None,
            "date_from": None,
            "date_to": None,
            "show_all": True  # По умолчанию показываем все заказы
        }
        
        # Setup UI
        self._setup_ui()
        
        # Load data
        self.load_orders()
        self.load_filters()

    def _setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)  # Увеличиваем отступы для лучшего вида
        layout.setSpacing(15)  # Увеличиваем расстояние между элементами
        
        # Title area
        title_layout = QHBoxLayout()
        title = StrongBodyLabel("Список заказов")
        title.setObjectName("SectionTitle")
        title_layout.addWidget(title)
        
        # Add show MY orders toggle (обратная логика: теперь показываем все заказы по умолчанию)
        self.show_all_switch = SwitchButton("Мои заказы")
        self.show_all_switch.setChecked(False)  # По умолчанию выключен (показываем все)
        self.show_all_switch.checkedChanged.connect(self._on_show_my_toggled)
        title_layout.addWidget(self.show_all_switch)
        title_layout.addStretch(1)
        
        # Refresh button
        self.refresh_btn = ToolButton(FluentIcon.SYNC)
        self.refresh_btn.clicked.connect(self.load_orders)
        title_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(title_layout)
        
        # Statistics cards in horizontal layout
        stats_card = CardWidget()
        stats_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        stats_layout = QHBoxLayout(stats_card)
        stats_layout.setContentsMargins(15, 15, 15, 15)
        stats_layout.setSpacing(15)
        
        self.stats_layout = stats_layout
        layout.addWidget(stats_card)
        
        # Filters area
        self.filter_card = CardWidget()
        self.filter_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        filter_layout = QVBoxLayout(self.filter_card)
        filter_layout.setContentsMargins(15, 15, 15, 15)
        
        filter_header = QHBoxLayout()
        filter_header.addWidget(SubtitleLabel("Фильтры"))
        filter_header.addStretch(1)
        filter_layout.addLayout(filter_header)
        
        # Filter form layout
        filter_form = QFormLayout()
        filter_form.setVerticalSpacing(10)  # Увеличиваем расстояние между элементами формы
        filter_form.setHorizontalSpacing(15)
        filter_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Status filter
        self.status_combo = ComboBox()
        self.status_combo.addItem("Все статусы", None)
        self.status_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_form.addRow("Статус:", self.status_combo)
        
        # Client filter
        self.client_combo = ComboBox()
        self.client_combo.addItem("Все клиенты", None)
        self.client_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_form.addRow("Клиент:", self.client_combo)
        
        # Date range
        date_range_layout = QHBoxLayout()
        date_range_layout.setSpacing(10)
        
        self.date_from = DateEdit()
        self.date_from.dateChanged.connect(self._on_filter_changed)
        
        self.date_to = DateEdit()
        self.date_to.dateChanged.connect(self._on_filter_changed)
        
        date_range_layout.addWidget(self.date_from)
        date_range_layout.addWidget(QLabel("-"))
        date_range_layout.addWidget(self.date_to)
        
        filter_form.addRow("Период:", date_range_layout)
        filter_layout.addLayout(filter_form)
        
        # Добавляем фильтры в основной макет
        layout.addWidget(self.filter_card)
        
        # Orders table - настраиваем на растягивание
        self.orders_table = TableWidget()
        self.orders_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.orders_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.orders_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.orders_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.orders_table.verticalHeader().setVisible(False)
        
        # Настройка растягивания таблицы
        self.orders_table.horizontalHeader().setStretchLastSection(True)
        
        self._setup_order_table()
        
        # Добавляем таблицу с большим коэффициентом растяжения
        layout.addWidget(self.orders_table, 1)  # Значение 1 дает максимальный приоритет растяжения
        
        # Progress bar
        self.progress_bar = IndeterminateProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def _on_show_my_toggled(self, checked):
        # Инвертируем логику: если тумблер включен, показываем только заказы текущего сотрудника
        self.filters["show_all"] = not checked
        self.load_orders()

    def load_orders(self):
        """Load orders based on current filters"""
        self.progress_bar.setVisible(True)
        
        # Clear table
        while self.orders_table.rowCount() > 0:
            self.orders_table.removeRow(0)
            
        try:
            db = SessionLocal()
            
            # Get worker ID from user_data
            worker_id = self.user_data.get('id')
            
            # Apply filters
            status = self.filters.get("status")
            client_id = self.filters.get("client_id")
            date_from = self.filters.get("date_from")
            date_to = self.filters.get("date_to")
            show_all = self.filters.get("show_all", True)  # По умолчанию показываем все заказы
            
            # Get orders
            if show_all:
                # Get all orders if show_all is enabled
                orders = self.order_controller.get_filtered_orders(
                    db, status=status, client_id=client_id,
                    date_from=date_from, date_to=date_to
                )
            else:
                # Get only worker's orders
                orders = self.order_controller.get_filtered_orders(
                    db, worker_id=worker_id, status=status, client_id=client_id,
                    date_from=date_from, date_to=date_to
                )
            
            # Populate table
            for i, order in enumerate(orders):
                self.orders_table.insertRow(i)
                
                # Order ID
                self.orders_table.setItem(i, 0, QTableWidgetItem(str(order.id)))
                
                # Client
                client_name = f"{order.client.first} {order.client.last}" if order.client else "Н/Д"
                self.orders_table.setItem(i, 1, QTableWidgetItem(client_name))
                
                # Date
                date_str = order.date.strftime("%d.%m.%Y %H:%M") if order.date else "Н/Д"
                self.orders_table.setItem(i, 2, QTableWidgetItem(date_str))
                
                # Worker
                worker_name = f"{order.worker.first} {order.worker.last}" if order.worker else "Не назначен"
                self.orders_table.setItem(i, 3, QTableWidgetItem(worker_name))
                
                # Status
                self.orders_table.setItem(i, 4, QTableWidgetItem(order.status))
                
                # Actions
                actions_widget = self._create_order_actions(i, order)
                self.orders_table.setCellWidget(i, 5, actions_widget)
                
            # Update statistics
            self._update_statistics(db)
            
            if len(orders) == 0:
                InfoBar.info(
                    title="Информация",
                    content="Заказы не найдены",
                    parent=self
                )
                
        except Exception as e:
            InfoBar.error(
                title="Ошибка",
                content=f"Не удалось загрузить заказы: {str(e)}",
                parent=self
            )
        finally:
            db.close()
            self.progress_bar.setVisible(False)

    def _update_statistics(self, db):
        """Update order statistics cards"""
        # Clear previous stats
        for i in reversed(range(self.stats_layout.count())): 
            if self.stats_layout.itemAt(i).widget():
                self.stats_layout.itemAt(i).widget().setParent(None)
        
        worker_id = None if self.filters.get("show_all", True) else self.user_data.get('id')
        
        # Count orders by status
        new_count = self.order_controller.count_by_status(db, "new", worker_id)
        in_progress_count = self.order_controller.count_by_status(db, "in_progress", worker_id)
        completed_count = self.order_controller.count_by_status(db, "completed", worker_id)
        cancelled_count = self.order_controller.count_by_status(db, "cancelled", worker_id)
        total_count = new_count + in_progress_count + completed_count + cancelled_count
        
        # Создаем карточки статистики с корректными иконками (без COMPLETE/DONE)
        self._add_stat_card("Всего заказов", total_count, FluentIcon.VIEW)
        self._add_stat_card("В работе", in_progress_count, FluentIcon.CONSTRACT)
        self._add_stat_card("Выполненные", completed_count, FluentIcon.CHECKBOX) # Используем CHECK вместо DONE/COMPLETE
        self._add_stat_card("Отмененные", cancelled_count, FluentIcon.CANCEL)

    def _add_stat_card(self, title, count, icon):
        """Add a statistics card"""
        card_widget = QWidget()
        card_widget.setObjectName("StatCard")
        card_widget.setStyleSheet("""
            #StatCard {
                background: #f9f9f9;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)
        card_widget.setFixedHeight(60)
        card_widget.setMinimumWidth(100)
        
        layout = QHBoxLayout(card_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Создаем иконку напрямую через ToolButton
        icon_btn = ToolButton(icon)
        icon_btn.setIconSize(QSize(24, 24))
        icon_btn.setEnabled(True)
        icon_btn.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(icon_btn)
        
        # Text layout
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        
        # Title
        title_label = BodyLabel(title)
        text_layout.addWidget(title_label)
        
        # Count
        count_label = StrongBodyLabel(str(count))
        text_layout.addWidget(count_label)
        
        layout.addLayout(text_layout)
        layout.addStretch(1)
        
        self.stats_layout.addWidget(card_widget, 1)  # Растягиваем все карточки одинаково

    def _on_filter_changed(self):
        self.load_orders()

    def _setup_order_table(self):
        """Setup order table columns and headers"""
        self.orders_table.setColumnCount(6)
        self.orders_table.setHorizontalHeaderLabels([
            "ID", "Клиент", "Дата", "Сотрудник", 
            "Статус", "Действия"
        ])
        
        # Set column widths
        self.orders_table.setColumnWidth(0, 80)  # ID
        self.orders_table.setColumnWidth(1, 160)  # Client
        self.orders_table.setColumnWidth(2, 140)  # Date
        self.orders_table.setColumnWidth(3, 160)  # Worker
        self.orders_table.setColumnWidth(4, 120)  # Status
        self.orders_table.setColumnWidth(5, 80)   # Actions
        
        # Enable sorting
        self.orders_table.setSortingEnabled(True)
        
        # Делаем нужные колонки растягиваемыми
        header = self.orders_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)

    def _create_order_actions(self, row, order):
        """Create action buttons for order row"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(0)
        
        # Edit button - только одна кнопка "Редактировать"
        edit_btn = TransparentToolButton(FluentIcon.EDIT)
        edit_btn.setIconSize(QSize(20, 20))
        edit_btn.setToolTip("Редактировать заказ")
        edit_btn.clicked.connect(lambda: self._edit_order(order.id))
        edit_btn.setStyleSheet("""
            TransparentToolButton {
                padding: 4px;
                border-radius: 4px;
            }
            TransparentToolButton:hover {
                background-color: #e6f2ff;
            }
        """)
        layout.addWidget(edit_btn)
        
        return widget

    def _show_order_details(self, order_id):
        """Show order details"""
        dialog = OrderDetailsDialog(order_id, self.user_data, self)
        dialog.exec()
        
    def _edit_order(self, order_id):
        """Edit order"""
        dialog = OrderDetailsDialog(order_id, self.user_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_orders()
            
    def _change_order_status(self, order_id, current_status):
        """Open dialog to change order status"""
        dialog = ChangeStatusDialog(order_id, current_status, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_orders()
            
    def _start_order_work(self, order_id):
        # Implementation of starting order work
        pass
        
    def _complete_order(self, order_id):
        # Implementation of completing order
        pass

    def generate_statement(self, order_id):
        """Generate statement document for client"""
        try:
            db = SessionLocal()
            order = self.order_controller.get_by_id(db, order_id)
            if not order:
                InfoBar.error(
                    title="Ошибка",
                    content="Заказ не найден",
                    parent=self
                )
                return
                
            # Generate PDF statement using document generator
            from ...common.utils.document_generator import generate_order_statement
            pdf_path = generate_order_statement(order)
            
            if not pdf_path:
                InfoBar.error(
                    title="Ошибка",
                    content="Не удалось создать документ",
                    parent=self
                )
                return
            
            # Open PDF file
            try:
                import platform
                import subprocess
                
                if platform.system() == 'Windows':
                    os.startfile(pdf_path)
                elif platform.system() == 'Darwin':
                    subprocess.call(('open', pdf_path))
                else:
                    subprocess.call(('xdg-open', pdf_path))
                    
                InfoBar.success(
                    title="Успех",
                    content=f"Акт выполненных работ сохранен: {pdf_path}",
                    parent=self
                )
            except Exception as e:
                InfoBar.warning(
                    title="Предупреждение",
                    content=f"Файл сохранен как {pdf_path}, но не удалось открыть его автоматически: {e}",
                    parent=self
                )
            
        except Exception as e:
            InfoBar.error(
                title="Ошибка",
                content=f"Не удалось сформировать акт: {str(e)}",
                parent=self
            )
        finally:
            db.close()
            
    def delete_order(self, order_id):
        """Delete order after confirmation"""
        confirm = MessageBox(
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить заказ? Это действие нельзя отменить.",
            self
        )
        
        if confirm.exec():
            try:
                db = SessionLocal()
                result = self.order_controller.delete(db, order_id)
                if result:
                    InfoBar.success(
                        title="Успех",
                        content="Заказ успешно удален",
                        parent=self
                    )
                    self.load_orders()
                else:
                    InfoBar.error(
                        title="Ошибка",
                        content="Не удалось удалить заказ",
                        parent=self
                    )
            except Exception as e:
                InfoBar.error(
                    title="Ошибка",
                    content=f"Не удалось удалить заказ: {str(e)}",
                    parent=self
                )
            finally:
                db.close()

    def load_filters(self):
        """Load filter options from database"""
        try:
            db = SessionLocal()
            
            # Load status options
            self.status_combo.clear()
            self.status_combo.addItem("Все статусы", None)
            self.status_combo.addItem("В работе", "in_progress") 
            self.status_combo.addItem("Завершенные", "completed")
            self.status_combo.addItem("Отмененные", "cancelled")
            
            # Load client options
            self.client_combo.clear()
            self.client_combo.addItem("Все клиенты", None)
            
            clients = self.client_controller.get_all(db)
            for client in clients:
                self.client_combo.addItem(
                    f"{client.first} {client.last}", 
                    client.id
                )
                
        except Exception as e:
            InfoBar.error(
                title="Ошибка",
                content=f"Не удалось загрузить фильтры: {str(e)}",
                parent=self
            )
        finally:
            db.close()


class OrderDetailsDialog(QDialog):
    def __init__(self, order_id, user_data, parent=None):
        super().__init__(parent=parent)
        self.order_id = order_id
        self.user_data = user_data
        
        # Initialize controllers
        self.order_controller = OrderController()
        self.client_controller = ClientController()
        self.worker_controller = WorkerController()
        self.material_controller = MaterialController()
        
        # Set dialog properties
        self.setWindowTitle("Детали заказа")
        self.resize(600, 600)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # Setup UI
        self._setup_ui()
        
        # Load order data
        self.load_order_data()
        
    def _setup_ui(self):
        # Order ID header
        id_layout = QHBoxLayout()
        id_label = SubtitleLabel("ID заказа:")
        self.order_id_label = BodyLabel("")
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.order_id_label)
        id_layout.addStretch(1)
        self.main_layout.addLayout(id_layout)
        
        # Add scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        
        # Client section
        client_card = CardWidget()
        client_layout = QVBoxLayout(client_card)
        client_layout.setContentsMargins(15, 15, 15, 15)
        
        client_header = QHBoxLayout()
        client_icon = ToolButton(FluentIcon.PEOPLE)
        client_icon.setStyleSheet("background: transparent; border: none;")
        client_title = SubtitleLabel("Информация о клиенте")
        client_header.addWidget(client_icon)
        client_header.addWidget(client_title)
        client_header.addStretch()
        client_layout.addLayout(client_header)
        
        client_form = QFormLayout()
        client_form.setVerticalSpacing(10)
        client_form.setHorizontalSpacing(15)
        
        self.client_label = BodyLabel("")
        self.phone_label = BodyLabel("")
        self.address_label = BodyLabel("")
        
        client_form.addRow(StrongBodyLabel("Клиент:"), self.client_label)
        client_form.addRow(StrongBodyLabel("Телефон:"), self.phone_label)
        client_form.addRow(StrongBodyLabel("Адрес:"), self.address_label)
        
        client_layout.addLayout(client_form)
        scroll_layout.addWidget(client_card)
        
        # Order details section
        order_card = CardWidget()
        order_layout = QVBoxLayout(order_card)
        order_layout.setContentsMargins(15, 15, 15, 15)
        
        order_header = QHBoxLayout()
        order_icon = ToolButton(FluentIcon.DOCUMENT)
        order_icon.setStyleSheet("background: transparent; border: none;")
        order_title = SubtitleLabel("Информация о заказе")
        order_header.addWidget(order_icon)
        order_header.addWidget(order_title)
        order_header.addStretch()
        order_layout.addLayout(order_header)
        
        order_form = QFormLayout()
        order_form.setVerticalSpacing(10)
        order_form.setHorizontalSpacing(15)
        
        self.date_label = BodyLabel("")
        
        # Status with editable combobox
        status_layout = QHBoxLayout()
        self.status_combo = ComboBox()
        for status in [s.value for s in OrderStatus]:
            self.status_combo.addItem(status)
        status_layout.addWidget(self.status_combo)
        status_layout.addStretch()
        
        self.worker_label = BodyLabel("")
        self.period_label = BodyLabel("")
        
        # Comment can be edited
        self.comment_edit = LineEdit()
        self.comment_edit.setPlaceholderText("Добавить комментарий")
        
        order_form.addRow(StrongBodyLabel("Дата заказа:"), self.date_label)
        order_form.addRow(StrongBodyLabel("Статус:"), status_layout)
        order_form.addRow(StrongBodyLabel("Сотрудник:"), self.worker_label)
        order_form.addRow(StrongBodyLabel("Срок выполнения (дней):"), self.period_label)
        order_form.addRow(StrongBodyLabel("Комментарий:"), self.comment_edit)
        
        order_layout.addLayout(order_form)
        scroll_layout.addWidget(order_card)
        
        # Materials section
        materials_card = CardWidget()
        materials_layout = QVBoxLayout(materials_card)
        materials_layout.setContentsMargins(15, 15, 15, 15)
        
        materials_header = QHBoxLayout()
        materials_icon = ToolButton(FluentIcon.BOOK_SHELF)
        materials_icon.setStyleSheet("background: transparent; border: none;")
        materials_title = SubtitleLabel("Материалы")
        materials_header.addWidget(materials_icon)
        materials_header.addWidget(materials_title)
        materials_header.addStretch()
        materials_layout.addLayout(materials_header)
        
        self.materials_table = TableWidget()
        self.materials_table.setColumnCount(4)
        self.materials_table.setHorizontalHeaderLabels(['Материал', 'Количество', 'Цена', 'Стоимость'])
        self.materials_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.materials_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.materials_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.materials_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.materials_table.setColumnWidth(1, 100)
        self.materials_table.setColumnWidth(2, 100)
        self.materials_table.setColumnWidth(3, 100)
        
        materials_layout.addWidget(self.materials_table)
        
        # Total cost 
        cost_layout = QHBoxLayout()
        cost_layout.addStretch()
        cost_label = StrongBodyLabel("Итого:")
        self.total_cost_label = SubtitleLabel("")
        cost_layout.addWidget(cost_label)
        cost_layout.addWidget(self.total_cost_label)
        
        materials_layout.addLayout(cost_layout)
        scroll_layout.addWidget(materials_card)
        
        # Set the content widget
        scroll_area.setWidget(scroll_content)
        self.main_layout.addWidget(scroll_area, 1)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 10, 0, 0)
        
        self.statement_btn = PushButton("Сформировать акт")
        self.statement_btn.clicked.connect(lambda: self.generate_statement(self.order_id))
        
        self.save_btn = PrimaryPushButton("Сохранить изменения")
        self.save_btn.clicked.connect(self.save_changes)
        
        self.close_btn = PushButton("Закрыть")
        self.close_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.statement_btn)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.close_btn)
        
        self.main_layout.addLayout(buttons_layout)
        
    def load_order_data(self):
        """Load order data from database"""
        try:
            db = SessionLocal()
            
            # Load order
            order = self.order_controller.get_by_id(db, self.order_id)
            if not order:
                InfoBar.error(
                    title="Ошибка",
                    content="Заказ не найден",
                    parent=self
                )
                self.reject()
                return
                
            # Set form values
            self.order_id_label.setText(str(order.id))
            self.client_label.setText(f"{order.client.first} {order.client.last}" if order.client else "Н/Д")
            self.phone_label.setText(order.client.phone if order.client and order.client.phone else "Не указан")
            self.address_label.setText("ул. Примерная, д. 123, офис 45")
            
            self.date_label.setText(order.date.strftime("%d.%m.%Y %H:%M") if order.date else "Н/Д")
            
            # Set status combobox
            self.current_status = order.status
            index = self.status_combo.findText(order.status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
            
            # Set worker info
            if order.worker:
                self.worker_label.setText(f"{order.worker.first} {order.worker.last}")
            elif self.user_data.get('id'):
                # If no worker assigned but we're viewing as a worker, show current user
                worker = self.worker_controller.get_by_id(db, self.user_data.get('id'))
                if worker:
                    self.worker_label.setText(f"{worker.first} {worker.last} (Текущий пользователь)")
                else:
                    self.worker_label.setText("Не назначен")
            else:
                self.worker_label.setText("Не назначен")
            
            if order.prod_period:
                self.period_label.setText(str(order.prod_period))
            
            # Set comment
            self.comment_edit.setText(order.comment if order.comment else "")
            
            # Load materials for the table
            self.materials_table.clearContents()
            self.materials_table.setRowCount(0)
            
            materials_total = 0
            materials_list = []
            
            # Check for materials from different possible attributes
            if hasattr(order, 'materials_on_order') and order.materials_on_order:
                materials_list = order.materials_on_order
            elif hasattr(order, 'materials_link') and order.materials_link:
                materials_list = order.materials_link
            
            # Add rows for materials
            for i, mat in enumerate(materials_list):
                if hasattr(mat, 'material') and mat.material:
                    material = mat.material
                    material_type = material.type
                    amount = mat.amount
                    price = material.price
                    cost = amount * price
                    materials_total += cost
                    
                    self.materials_table.insertRow(i)
                    self.materials_table.setItem(i, 0, QTableWidgetItem(material_type))
                    self.materials_table.setItem(i, 1, QTableWidgetItem(str(amount)))
                    self.materials_table.setItem(i, 2, QTableWidgetItem(f"{price} ₽"))
                    self.materials_table.setItem(i, 3, QTableWidgetItem(f"{cost} ₽"))
            
            # Update total cost
            self.total_cost_label.setText(f"{materials_total} ₽")
            
            # Disable editing if order is completed
            if order.status == OrderStatus.COMPLETED.value:
                self.status_combo.setEnabled(False)
                self.comment_edit.setReadOnly(True)
                self.save_btn.setEnabled(False)
                
                InfoBar.warning(
                    title="Внимание",
                    content="Заказ уже выполнен. Изменения невозможны.",
                    parent=self
                )
            
        except Exception as e:
            InfoBar.error(
                title="Ошибка",
                content=f"Не удалось загрузить данные заказа: {str(e)}",
                parent=self
            )
            self.reject()
        finally:
            db.close()
    
    def save_changes(self):
        """Save changes to order"""
        try:
            # Check if status changed
            new_status = self.status_combo.currentText()
            new_comment = self.comment_edit.text().strip()
            
            # If nothing changed, just close
            if new_status == self.current_status and not new_comment:
                self.accept()
                return
                
            db = SessionLocal()
            
            # Create update data
            update_data = OrderUpdate(
                status=new_status,
                comment=new_comment if new_comment else None
            )
            
            # Update order
            result = self.order_controller.update(db, self.order_id, update_data)
            
            if result:
                InfoBar.success(
                    title="Успех",
                    content="Заказ успешно обновлен",
                    parent=self
                )
                self.accept()
            else:
                InfoBar.error(
                    title="Ошибка",
                    content="Не удалось обновить заказ",
                    parent=self
                )
        except Exception as e:
            InfoBar.error(
                title="Ошибка",
                content=f"Не удалось обновить заказ: {str(e)}",
                parent=self
            )
        finally:
            db.close()
    
    def generate_statement(self, order_id):
        """Generate statement document for client"""
        try:
            db = SessionLocal()
            order = self.order_controller.get_by_id(db, order_id)
            if not order:
                InfoBar.error(
                    title="Ошибка",
                    content="Заказ не найден",
                    parent=self
                )
                return
                
            # Generate statement using document generator
            from ...common.utils.document_generator import generate_order_statement
            pdf_path = generate_order_statement(order)
            
            if not pdf_path:
                InfoBar.error(
                    title="Ошибка",
                    content="Не удалось создать документ",
                    parent=self
                )
                return
            
            # Open the generated file
            try:
                import platform
                import subprocess
                
                if platform.system() == 'Windows':
                    os.startfile(pdf_path)
                elif platform.system() == 'Darwin':
                    subprocess.call(('open', pdf_path))
                else:
                    subprocess.call(('xdg-open', pdf_path))
                    
                InfoBar.success(
                    title="Успех",
                    content=f"Документ сохранен: {pdf_path}",
                    parent=self
                )
            except Exception as e:
                InfoBar.warning(
                    title="Предупреждение",
                    content=f"Файл сохранен как {pdf_path}, но не удалось открыть его автоматически: {e}",
                    parent=self
                )
            
        except Exception as e:
            InfoBar.error(
                title="Ошибка",
                content=f"Не удалось создать документ: {str(e)}",
                parent=self
            )
        finally:
            db.close()


class ChangeStatusDialog(QDialog):
    def __init__(self, order_id, current_status, parent=None):
        super().__init__(parent=parent)
        self.order_id = order_id
        self.current_status = current_status
        
        # Initialize controllers
        self.order_controller = OrderController()
        
        # Set dialog properties
        self.setWindowTitle("Изменение статуса заказа")
        self.resize(400, 200)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        # Header with icon
        header_layout = QHBoxLayout()
        header_icon = ToolButton(FluentIcon.TAG)
        header_icon.setStyleSheet("background: transparent; border: none;")
        header_title = SubtitleLabel("Изменение статуса заказа")
        header_layout.addWidget(header_icon)
        header_layout.addWidget(header_title)
        header_layout.addStretch(1)
        self.layout.addLayout(header_layout)
        
        # Instructions
        instruction = BodyLabel("Выберите новый статус для заказа:")
        self.layout.addWidget(instruction)
        
        # Status combo box
        self.status_combo = ComboBox(self)
        for status in [s.value for s in OrderStatus]:
            self.status_combo.addItem(status)
            
        # Set current status
        index = self.status_combo.findText(self.current_status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)
            
        self.layout.addWidget(self.status_combo)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Cancel button
        cancel_button = PushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # Spacer
        button_layout.addStretch()
        
        # Save button
        self.save_button = PrimaryPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_status)
        button_layout.addWidget(self.save_button)
        
        self.layout.addLayout(button_layout)
        
    def save_status(self):
        """Save new status"""
        new_status = self.status_combo.currentText()
        
        # No change
        if new_status == self.current_status:
            self.accept()
            return
            
        try:
            db = SessionLocal()
            
            # Update status
            update_data = OrderUpdate(status=new_status)
            result = self.order_controller.update(db, self.order_id, update_data)
            
            if result:
                InfoBar.success(
                    title="Успех",
                    content=f"Статус заказа изменен на: {new_status}",
                    parent=self
                )
                self.accept()
            else:
                InfoBar.error(
                    title="Ошибка",
                    content="Не удалось обновить статус заказа",
                    parent=self
                )
        except Exception as e:
            InfoBar.error(
                title="Ошибка",
                content=f"Не удалось обновить статус заказа: {str(e)}",
                parent=self
            )
        finally:
            db.close() 