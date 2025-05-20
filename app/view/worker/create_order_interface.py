from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtGui import QIcon, QFont, QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QDateEdit, QPushButton, QLineEdit, QDialog, QMessageBox,
    QSpinBox, QFormLayout, QScrollArea
)

from qfluentwidgets import (
    FluentIcon, InfoBar, Dialog, ComboBox, 
    PushButton, TableWidget, LineEdit, SpinBox, 
    DateEdit, SearchLineEdit, MessageBox, IndeterminateProgressBar,
    StrongBodyLabel, BodyLabel, CaptionLabel, SubtitleLabel,
    PrimaryPushButton, PushButton, CardWidget, InfoBarPosition
)

from ...common.db.controller import OrderController, ClientController, WorkerController, MaterialController
from ...common.db.models_pydantic import OrderStatus, OrderCreate, MaterialOnOrderCreate
from ...common.db.database import SessionLocal
from ...common.signal_bus import signalBus
import uuid
from datetime import datetime
import fpdf
import os
import tempfile
import os.path

class CreateOrderInterface(QWidget):
    def __init__(self, user_data, parent=None):
        super().__init__(parent=parent)
        self.user_data = user_data
        
        # Initialize controllers
        self.order_controller = OrderController()
        self.client_controller = ClientController()
        self.worker_controller = WorkerController()
        self.material_controller = MaterialController()
        
        # Initialize material list for order
        self.order_materials = []
        
        # Отслеживание выбранного клиента
        self.selected_client_id = None
        # Словарь для хранения ID клиентов по индексам
        self.client_ids = {}
        
        # --- Main Scroll Area Setup ---
        # This will be the new top-level layout for CreateOrderInterface
        outer_layout = QVBoxLayout(self) 
        outer_layout.setContentsMargins(0,0,0,0) # No margins for the layout holding the scroll area
        self.setLayout(outer_layout) # Apply it to self

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("createOrderScrollArea")
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        outer_layout.addWidget(scroll_area)

        # This widget will contain all the actual UI content and will be set into the scroll_area
        self.scroll_content_widget = QWidget()
        scroll_area.setWidget(self.scroll_content_widget)
        
        # The original main layout is now applied to self.scroll_content_widget
        # All UI elements will be added to this 'content_layout'
        self.content_layout = QVBoxLayout(self.scroll_content_widget) 
        # self._setup_ui() will now populate self.content_layout

        # Setup UI (which now populates self.content_layout)
        self._setup_ui()
        
        # Load clients and materials
        self.load_clients()
        self.load_materials()
        
    def _setup_ui(self):
        # Main layout is now self.content_layout, taken from __init__
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(FluentIcon.ADD.icon().pixmap(32, 32))
        title_label = SubtitleLabel("Создание нового заказа")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch(1)
        self.content_layout.addLayout(title_layout)
        
        # Create main card for client and order info
        client_card = CardWidget()
        client_card_layout = QVBoxLayout(client_card)
        client_card_layout.setContentsMargins(20, 20, 20, 20)
        client_card_layout.setSpacing(15)
        
        # Section title for client info
        client_section = StrongBodyLabel("Информация о заказе")
        client_section.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        client_card_layout.addWidget(client_section)
        
        # Form layout for client info
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(20)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Set font for labels
        label_font = QFont("Segoe UI", 11)
        input_font = QFont("Segoe UI", 11)
        
        # Client selection with improved styling
        client_label = QLabel("Клиент*:")
        client_label.setFont(label_font)
        
        # Добавляем контейнер для поиска и выбора клиента
        client_selection_layout = QVBoxLayout()
        client_selection_layout.setSpacing(8)
        
        # Поле поиска клиентов
        self.client_search = SearchLineEdit(self)
        self.client_search.setPlaceholderText("Поиск клиентов...")
        self.client_search.setFont(input_font)
        self.client_search.setMinimumHeight(36)
        self.client_search.textChanged.connect(self.filter_clients)
        self.client_search.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d4d4d4;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
            }
            QLineEdit:hover {
                border: 1px solid #0078d4;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
            }
        """)
        client_selection_layout.addWidget(self.client_search)
        
        # Комбобокс с клиентами
        self.client_combo = ComboBox(self)
        self.client_combo.setMinimumWidth(300)
        self.client_combo.setMinimumHeight(36)
        self.client_combo.setFont(input_font)
        self.client_combo.currentIndexChanged.connect(self.on_client_selected)
        client_selection_layout.addWidget(self.client_combo)
        
        form_layout.addRow(client_label, client_selection_layout)
        
        # Employee accepting order
        employee_label = QLabel("Сотрудник:")
        employee_label.setFont(label_font)
        
        employee_name = f"{self.user_data.get('first', '')} {self.user_data.get('last', '')}"
        employee_field = LineEdit(self)
        employee_field.setText(employee_name)
        employee_field.setReadOnly(True)
        employee_field.setFont(input_font)
        employee_field.setMinimumHeight(36)
        employee_field.setStyleSheet("background-color: #f0f0f0;") # Visually indicate read-only
        
        form_layout.addRow(employee_label, employee_field)
        
        # Production period with improved input
        period_label = QLabel("Срок выполнения (дней)*:")
        period_label.setFont(label_font)
        
        self.period_spin = SpinBox(self)
        self.period_spin.setRange(1, 365)
        self.period_spin.setValue(7)  # Default: 1 week
        self.period_spin.setFont(input_font)
        self.period_spin.setMinimumHeight(36)
        self.period_spin.setSuffix(" дней")  # Add suffix for clarity
        
        form_layout.addRow(period_label, self.period_spin)
        
        client_card_layout.addLayout(form_layout)
        self.content_layout.addWidget(client_card)
        
        # --- Materials Section with ScrollArea (This inner scroll area is no longer needed if the whole page scrolls) ---
        # The previous change for an inner scroll area for materials is now superseded by the whole-page scroll.
        # So, we revert the materials_card to be added directly to self.content_layout.

        # Materials section in its own card
        materials_card = CardWidget()
        materials_card_layout = QVBoxLayout(materials_card)
        materials_card_layout.setContentsMargins(20, 20, 20, 20)
        materials_card_layout.setSpacing(15)
        
        # Materials title with icon
        materials_title_layout = QHBoxLayout()
        materials_icon = QLabel()
        materials_icon.setPixmap(FluentIcon.BOOK_SHELF.icon().pixmap(24, 24))
        materials_title = StrongBodyLabel("Материалы для заказа")
        materials_title.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        materials_title_layout.addWidget(materials_icon)
        materials_title_layout.addWidget(materials_title)
        materials_title_layout.addStretch(1)
        materials_card_layout.addLayout(materials_title_layout)
        
        # Available materials
        materials_layout = QHBoxLayout()
        materials_layout.setSpacing(20)
        
        # Materials selection
        material_selection_layout = QVBoxLayout()
        material_selection_layout.setSpacing(12)
        
        # Material combo
        material_combo_label = QLabel("Выберите материал:")
        material_combo_label.setFont(label_font)
        material_selection_layout.addWidget(material_combo_label)
        
        self.material_combo = QComboBox(self)
        self.material_combo.setMinimumWidth(300)
        self.material_combo.setMinimumHeight(36)
        self.material_combo.setFont(input_font)
        self.material_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d4d4d4;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
            }
            QComboBox:hover {
                border: 1px solid #0078d4;
            }
            QComboBox:focus {
                border: 1px solid #0078d4;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        material_selection_layout.addWidget(self.material_combo)
        
        # Quantity spin
        quantity_label = QLabel("Количество:")
        quantity_label.setFont(label_font)
        material_selection_layout.addWidget(quantity_label)
        
        self.quantity_spin = SpinBox(self)
        self.quantity_spin.setRange(1, 1000)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setFont(input_font)
        self.quantity_spin.setMinimumHeight(36)
        self.quantity_spin.setSuffix(" шт.")  # Add suffix for clarity
        material_selection_layout.addWidget(self.quantity_spin)
        
        # Add material button
        add_material_button = PrimaryPushButton("Добавить материал в заказ")
        add_material_button.setIcon(FluentIcon.ADD)
        add_material_button.setFont(QFont("Segoe UI", 11))
        add_material_button.clicked.connect(self.add_material_to_order)
        add_material_button.setMinimumHeight(40)
        material_selection_layout.addWidget(add_material_button)
        
        materials_layout.addLayout(material_selection_layout, 1)
        
        # Selected materials table
        materials_table_layout = QVBoxLayout()
        materials_table_layout.setSpacing(10)
        materials_table_label = QLabel("Выбранные материалы:")
        materials_table_label.setFont(label_font)
        materials_table_layout.addWidget(materials_table_label)
        
        self.materials_table = TableWidget(self)
        self.materials_table.setColumnCount(5)
        self.materials_table.setHorizontalHeaderLabels([
            "ID", "Материал", "Количество", "Цена за ед.", "Сумма"
        ])
        self.materials_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.materials_table.verticalHeader().setVisible(False)
        self.materials_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.materials_table.setFont(QFont("Segoe UI", 11))
        self.materials_table.setMinimumHeight(150)  # Ensure table has sufficient vertical space
        
        # Style table header
        header = self.materials_table.horizontalHeader()
        header.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        
        # Hide ID column
        self.materials_table.setColumnHidden(0, True)
        
        materials_table_layout.addWidget(self.materials_table)
        
        # Remove material button
        remove_material_button = PushButton("Удалить выбранный материал")
        remove_material_button.setIcon(FluentIcon.DELETE)
        remove_material_button.clicked.connect(self.remove_material)
        remove_material_button.setFont(QFont("Segoe UI", 11))
        remove_material_button.setMinimumHeight(40)
        materials_table_layout.addWidget(remove_material_button)
        
        materials_layout.addLayout(materials_table_layout, 2)
        
        materials_card_layout.addLayout(materials_layout)
        self.content_layout.addWidget(materials_card)
        
        # Total cost in its own card with highlighted styling
        summary_card = CardWidget()
        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(20, 15, 20, 15)
        
        self.total_cost_label = StrongBodyLabel("Итого: 0 ₽")
        self.total_cost_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.total_cost_label.setStyleSheet("color: #0078d4;")  # Use theme color for emphasis
        summary_layout.addWidget(self.total_cost_label)
        
        self.content_layout.addWidget(summary_card)
        
        # Buttons with improved styling
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        # Clear form button
        clear_button = PushButton("Очистить форму")
        clear_button.setIcon(FluentIcon.DELETE)
        clear_button.clicked.connect(self.clear_form)
        clear_button.setFont(QFont("Segoe UI", 12))
        clear_button.setMinimumHeight(45)
        buttons_layout.addWidget(clear_button)
        
        buttons_layout.addStretch(1)
        
        # Create order button
        self.create_button = PrimaryPushButton("Создать заказ")
        self.create_button.setIcon(FluentIcon.SEND_FILL)
        self.create_button.clicked.connect(self.create_order)
        self.create_button.setFont(QFont("Segoe UI", 12))
        self.create_button.setMinimumHeight(45)
        self.create_button.setMinimumWidth(200)  # Make the primary action button wider
        buttons_layout.addWidget(self.create_button)
        
        self.content_layout.addLayout(buttons_layout)
        
        # Add progress bar for loading operations
        self.progress_bar = IndeterminateProgressBar(self)
        self.progress_bar.setVisible(False)
        self.content_layout.addWidget(self.progress_bar)
        
    def load_clients(self):
        """Load clients into combo box"""
        try:
            self.progress_bar.setVisible(True)
            db = SessionLocal()
            
            # Get all clients
            self.clients_list = self.client_controller.get_all(db)
            
            # Update combo box
            self.update_clients_combo(self.clients_list)
                
        except Exception as e:
            InfoBar.error(
                title="Ошибка",
                content=f"Не удалось загрузить клиентов: {str(e)}",
                parent=self
            )
        finally:
            self.progress_bar.setVisible(False)
    
    def update_clients_combo(self, clients):
        """Update client combo box with filtered clients list"""
        # Add to combo box
        self.client_combo.clear()
        # Очищаем словарь ID клиентов
        self.client_ids = {}
        
        self.client_combo.addItem("Выберите клиента", "")
        
        for client in clients:
            display_text = f"{client.first} {client.last}"
            if client.phone:
                display_text += f" ({client.phone})"
            elif client.mail:
                display_text += f" ({client.mail})"
                
            # Сохраняем ID как строку для надежности
            client_id = str(client.id)
            self.client_combo.addItem(display_text, client_id)
            
            # Сохраняем ID клиента в словарь
            self.client_ids[self.client_combo.count() - 1] = client_id
    
    def filter_clients(self, search_text):
        """Filter clients in combo box based on search text"""
        if not hasattr(self, 'clients_list') or not self.clients_list:
            return
            
        if not search_text.strip():
            # Если поиск пустой, показываем всех клиентов
            self.update_clients_combo(self.clients_list)
            return
            
        # Фильтруем клиентов по тексту поиска (имя, фамилия, телефон или email)
        search_text = search_text.lower().strip()
        filtered_clients = []
        
        for client in self.clients_list:
            # Проверяем совпадение в имени, фамилии, телефоне и email
            if (search_text in client.first.lower() or 
                search_text in client.last.lower() or
                (client.phone and search_text in client.phone.lower()) or
                (client.mail and search_text in client.mail.lower())):
                filtered_clients.append(client)
                
        # Обновляем комбобокс отфильтрованными клиентами
        self.update_clients_combo(filtered_clients)
        
        # Показываем сообщение, если ничего не найдено
        if not filtered_clients:
            InfoBar.info(
                title="Поиск",
                content=f"Клиенты по запросу '{search_text}' не найдены",
                parent=self,
                duration=3000
            )
            
    def load_materials(self):
        """Load materials into combo box"""
        try:
            self.progress_bar.setVisible(True)
            db = SessionLocal()
            
            # Get all materials
            materials = self.material_controller.get_all(db)
            
            # Add to combo box
            self.material_combo.clear()
            self.material_combo.addItem("Выберите материал", "")
            
            for material in materials:
                # Создаем отображаемый текст
                display_text = f"{material.type} (остаток: {material.balance}, цена: {material.price} ₽)"
                
                # Сохраняем данные как строковый идентификатор
                # ComboBox не поддерживает сложные данные, поэтому используем только ID
                self.material_combo.addItem(display_text, str(material.id))
                
                # Сохраняем полные данные в словаре для быстрого доступа
                if not hasattr(self, 'materials_data'):
                    self.materials_data = {}
                    
                # Храним все данные о материалах в словаре для доступа по id
                self.materials_data[str(material.id)] = {
                    'id': material.id,
                    'name': material.type,
                    'balance': material.balance,
                    'price': material.price
                }
                
        except Exception as e:
            InfoBar.error(
                title="Ошибка",
                content=f"Не удалось загрузить материалы: {str(e)}",
                parent=self
            )
        finally:
            self.progress_bar.setVisible(False)
            
    def add_material_to_order(self):
        """Add selected material to order"""
        # Get selected material
        selected_index = self.material_combo.currentIndex()
        material_id = self.material_combo.currentData()
        
        # Проверяем, выбран ли материал (индекс > 0 и данные не пустые)
        if selected_index <= 0 or not material_id:
            InfoBar.warning(
                title="Внимание",
                content="Выберите материал",
                parent=self
            )
            return
            
        # Получаем полные данные из нашего словаря
        try:
            material_data = self.materials_data[material_id]
            material_name = material_data['name']
            material_balance = material_data['balance']
            material_price = material_data['price']
        except Exception as e:
            InfoBar.error(
                title="Ошибка разбора данных",
                content=f"Не удалось найти данные материала: {str(e)}",
                parent=self
            )
            return
            
        # Get quantity
        quantity = self.quantity_spin.value()
        
        # Check if quantity is available
        if quantity > material_balance:
            InfoBar.warning(
                title="Внимание",
                content=f"Недостаточно материала на складе. Доступно: {material_balance}",
                parent=self
            )
            return
            
        # Check if material is already in the order
        for i, mat in enumerate(self.order_materials):
            if mat["id"] == material_id:
                # Update quantity if already in order
                new_quantity = mat["quantity"] + quantity
                if new_quantity > material_balance:
                    InfoBar.warning(
                        title="Внимание",
                        content=f"Недостаточно материала на складе. Доступно: {material_balance}",
                        parent=self
                    )
                    return
                
                self.order_materials[i]["quantity"] = new_quantity
                self.update_materials_table()
                return
        
        # Add new material to order
        material_item = {
            "id": material_id,
            "name": material_name,
            "quantity": quantity,
            "price": material_price,
            "total": quantity * material_price
        }
        
        self.order_materials.append(material_item)
        self.update_materials_table()
        
    def update_materials_table(self):
        """Update materials table and total cost"""
        # Clear table
        self.materials_table.setRowCount(0)
        
        # Add materials to table
        total_cost = 0
        for row, material in enumerate(self.order_materials):
            self.materials_table.insertRow(row)
            
            # ID (hidden)
            self.materials_table.setItem(row, 0, QTableWidgetItem(material["id"]))
            
            # Name
            self.materials_table.setItem(row, 1, QTableWidgetItem(material["name"]))
            
            # Quantity
            self.materials_table.setItem(row, 2, QTableWidgetItem(str(material["quantity"])))
            
            # Price
            self.materials_table.setItem(row, 3, QTableWidgetItem(f"{material['price']} ₽"))
            
            # Total
            material_total = material["quantity"] * material["price"]
            self.materials_table.setItem(row, 4, QTableWidgetItem(f"{material_total} ₽"))
            
            # Add to total cost
            total_cost += material_total
            
        # Update total cost label
        self.total_cost_label.setText(f"Итого: {total_cost} ₽")
        
    def remove_material(self):
        """Remove selected material from order"""
        selected_rows = self.materials_table.selectedIndexes()
        if not selected_rows:
            InfoBar.warning(
                title="Внимание",
                content="Выберите материал для удаления",
                parent=self
            )
            return
            
        # Get row index
        row = selected_rows[0].row()
        
        # Get material ID
        material_id = self.materials_table.item(row, 0).text()
        
        # Remove from order materials
        self.order_materials = [m for m in self.order_materials if m["id"] != material_id]
        
        # Update table
        self.update_materials_table()
        
    def clear_form(self):
        """Clear the form"""
        # Reset client selection
        self.client_combo.setCurrentIndex(0)
        
        # Reset production period
        self.period_spin.setValue(7)
        
        # Clear materials
        self.order_materials = []
        self.update_materials_table()
        
        # Show success message
        InfoBar.success(
            title="Форма очищена",
            content="Все поля формы были успешно сброшены.",
            parent=self,
            duration=3000, # Display for 3 seconds
            position=InfoBarPosition.TOP_RIGHT # Or other preferred position
        )
        
    def create_order(self):
        """Create new order"""
        # Validate form
        if not self.validate_form():
            return
            
        try:
            self.progress_bar.setVisible(True)
            db = SessionLocal()
            
            # Get form data using tracked client ID
            client_id = self.selected_client_id
            
            # Дополнительная проверка client_id
            if not client_id or client_id == "":
                InfoBar.error(
                    title="Ошибка",
                    content="Не выбран клиент для заказа",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
                return
                
            worker_id = self.user_data.get('id')
            prod_period = self.period_spin.value()
            
            # Convert materials to appropriate format
            materials = []
            for mat in self.order_materials:
                materials.append(
                    MaterialOnOrderCreate(
                        material_id=mat["id"],
                        amount=mat["quantity"]
                    )
                )
            
            # Create order data
            order_data = OrderCreate(
                id=str(uuid.uuid4()),
                client_id=str(client_id),
                worker_id=str(worker_id),
                prod_period=int(prod_period),
                status=OrderStatus.PROCESSING,
                materials=materials
            )
            
            # Добавляем дату создания заказа
            order_data_dict = order_data.model_dump()
            order_data_dict['date'] = datetime.now()
            
            # Create order
            result = self.order_controller.create(db, OrderCreate(**order_data_dict))
            
            if result:
                InfoBar.success(
                    title="Успех",
                    content=f"Заказ успешно создан",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
                
                # Ask if user wants to generate receipt
                confirm = MessageBox(
                    "Квитанция для клиента",
                    "Заказ успешно создан. Хотите сформировать квитанцию для клиента?",
                    self
                )
                
                if confirm.exec():
                    self.generate_receipt(result)
                
                # Clear form
                self.clear_form()
            else:
                InfoBar.error(
                    title="Ошибка",
                    content="Не удалось создать заказ",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=5000
                )
        except Exception as e:
            InfoBar.error(
                title="Ошибка",
                content=f"Не удалось создать заказ: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=5000
            )
        finally:
            self.progress_bar.setVisible(False)
            
    def validate_form(self):
        """Validate form data"""
        # Check client selection using tracked ID
        
        if not self.selected_client_id:
            InfoBar.warning(
                title="Внимание",
                content="Выберите клиента",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return False
            
        # Check if there are materials in the order
        if not self.order_materials:
            InfoBar.warning(
                title="Внимание",
                content="Добавьте материалы в заказ",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return False
            
        return True
        
    def generate_receipt(self, order):
        """Generate receipt document for client"""
        try:
            db = SessionLocal()
            
            # Get order with all related data
            order = self.order_controller.get_by_id(db, order.id)
            if not order:
                InfoBar.error(
                    title="Ошибка",
                    content="Заказ не найден",
                    parent=self
                )
                return
                
            # Generate PDF receipt using document generator
            from ...common.utils.document_generator import generate_order_receipt
            pdf_path = generate_order_receipt(order)
            
            if not pdf_path:
                InfoBar.error(
                    title="Ошибка",
                    content="Не удалось создать квитанцию",
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
                    content=f"Квитанция сохранена: {pdf_path}",
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
                content=f"Не удалось создать квитанцию: {str(e)}",
                parent=self
            )
            print(f"Error generating receipt: {str(e)}")
        finally:
            db.close()

    def on_client_selected(self, index):
        """Обработчик выбора клиента"""
        if index > 0:  # Если выбран реальный клиент (не первый пункт)
            if index in self.client_ids:
                self.selected_client_id = self.client_ids[index]
            else:
                self.selected_client_id = None
        else:
            self.selected_client_id = None 