from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize, QDate
from PyQt6.QtGui import QIcon
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
    PasswordLineEdit, InfoBarPosition
)

from ...common.db.controller import WorkerController
from ...common.db.models_pydantic import WorkerCreate, WorkerUpdate
from ...common.db.database import SessionLocal
from ...common.signal_bus import signalBus
import uuid
from datetime import datetime, timedelta
import re
import hashlib

class EmployeesInterface(QWidget):
    def __init__(self, user_data, parent=None):
        super().__init__(parent=parent)
        self.user_data = user_data
        
        # Make sure only directors can access this interface
        if self.user_data.get('position') != "Director":
            InfoBar.error(
                title="Доступ запрещен",
                content="Только директор может просматривать этот раздел",
                parent=self
            )
            return
        
        # Initialize controllers
        self.worker_controller = WorkerController()
        
        # Setup UI
        self._setup_ui()
        
        # Load employees
        self.load_employees()
        
    def _setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Director access notice
        director_notice = StrongBodyLabel("Только директор может управлять сотрудниками")
        director_notice.setStyleSheet("color: #e81123;")
        layout.addWidget(director_notice)
        
        # Header layout
        header_layout = QHBoxLayout()
        
        # Title
        title_label = SubtitleLabel("Управление сотрудниками")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Search field
        self.search_edit = SearchLineEdit(self)
        self.search_edit.setPlaceholderText("Поиск сотрудника")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self.load_employees)
        header_layout.addWidget(self.search_edit, 1)
        
        # Add employee button
        self.add_button = PushButton("Добавить сотрудника")
        self.add_button.setIcon(FluentIcon.ADD)
        self.add_button.clicked.connect(self.add_employee)
        header_layout.addWidget(self.add_button)
        
        layout.addLayout(header_layout)
        
        # Employees table
        self.employees_table = TableWidget(self)
        self.employees_table.setColumnCount(8)
        self.employees_table.setHorizontalHeaderLabels([
            "ID", "ФИО", "Должность", "Телефон", "Email", "Дата найма", "Дата рождения", "Действия"
        ])
        self.employees_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.employees_table.verticalHeader().setVisible(False)
        self.employees_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.employees_table.setSortingEnabled(True)
        
        # Adjust column widths
        self.employees_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        self.employees_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Actions
        
        layout.addWidget(self.employees_table)
        
        # Progress bar for loading
        self.progress_bar = IndeterminateProgressBar(self)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
    def load_employees(self):
        """Load employees from database with optional search filter"""
        self.progress_bar.setVisible(True)
        self.employees_table.setRowCount(0)
        
        try:
            db = SessionLocal()
            
            # Get search term
            search_term = self.search_edit.text().strip()
            
            # Get all employees (with filter if search term is provided)
            employees = self.worker_controller.get_all_filtered(db, search_term=search_term) if search_term else self.worker_controller.get_all(db)
            
            for row, employee in enumerate(employees):
                self.employees_table.insertRow(row)
                
                # ID
                self.employees_table.setItem(row, 0, QTableWidgetItem(str(employee.id)))
                
                # Full Name
                full_name = f"{employee.last} {employee.first}"
                if employee.middle:
                    full_name += f" {employee.middle}"
                self.employees_table.setItem(row, 1, QTableWidgetItem(full_name))
                
                # Position
                self.employees_table.setItem(row, 2, QTableWidgetItem(employee.position))
                
                # Phone
                self.employees_table.setItem(row, 3, QTableWidgetItem(employee.phone if employee.phone else ""))
                
                # Email
                self.employees_table.setItem(row, 4, QTableWidgetItem(employee.mail if employee.mail else ""))
                
                # Hire Date
                hire_date = employee.date.strftime("%d.%m.%Y") if employee.date else ""
                self.employees_table.setItem(row, 5, QTableWidgetItem(hire_date))
                
                # Birth Date
                birth_date = employee.born_date.strftime("%d.%m.%Y") if employee.born_date else ""
                self.employees_table.setItem(row, 6, QTableWidgetItem(birth_date))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                actions_layout.setSpacing(5)
                
                # Edit button
                edit_button = PushButton(text="")
                edit_button.setIcon(FluentIcon.EDIT)
                edit_button.setToolTip("Редактировать сотрудника")
                edit_button.clicked.connect(lambda _, emp_id=employee.id: self.edit_employee(emp_id))
                actions_layout.addWidget(edit_button)
                
                # Delete button
                delete_button = PushButton(text="")
                delete_button.setIcon(FluentIcon.DELETE)
                delete_button.setToolTip("Удалить сотрудника")
                delete_button.clicked.connect(lambda _, emp_id=employee.id: self.delete_employee(emp_id))
                actions_layout.addWidget(delete_button)
                
                self.employees_table.setCellWidget(row, 7, actions_widget)
            
        except Exception as e:
            InfoBar.error(
                title="Ошибка",
                content=f"Не удалось загрузить сотрудников: {str(e)}",
                parent=self
            )
        finally:
            self.progress_bar.setVisible(False)
            
    def add_employee(self):
        """Add new employee"""
        dialog = EmployeeDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_employees()
            
    def edit_employee(self, employee_id):
        """Edit existing employee"""
        dialog = EmployeeDialog(employee_id=employee_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_employees()
            
    def delete_employee(self, employee_id):
        """Delete employee after confirmation"""
        # Don't allow deleting self
        if employee_id == self.user_data.get('id'):
            InfoBar.error(
                title="Ошибка",
                content="Вы не можете удалить свою учетную запись",
                parent=self
            )
            return
            
        confirm = MessageBox(
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить сотрудника? Это действие нельзя отменить.",
            self
        )
        
        if confirm.exec():
            try:
                db = SessionLocal()
                result = self.worker_controller.delete(db, employee_id)
                if result:
                    InfoBar.success(
                        title="Успех",
                        content="Сотрудник успешно удален",
                        parent=self
                    )
                    self.load_employees()
                else:
                    InfoBar.error(
                        title="Ошибка",
                        content="Не удалось удалить сотрудника",
                        parent=self
                    )
            except Exception as e:
                InfoBar.error(
                    title="Ошибка",
                    content=f"Не удалось удалить сотрудника: {str(e)}",
                    parent=self
                )
            finally:
                db.close()


class EmployeeDialog(Dialog):
    def __init__(self, employee_id=None, parent=None):
        super().__init__(parent)
        self.employee_id = employee_id
        self.setTitle("Редактирование сотрудника" if employee_id else "Добавление сотрудника")
        self.resize(600, 650)
        
        # Initialize controller
        self.worker_controller = WorkerController()
        
        # Setup UI
        self._setup_ui()
        
        # Load employee data if editing
        if employee_id:
            self.load_employee_data()
        
    def _setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self.contentWidget)
        layout.setSpacing(15)
        
        # Scroll area
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(15)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(10)
        form_layout.setHorizontalSpacing(15)
        
        # Basic information section
        basic_info_label = StrongBodyLabel("Основная информация")
        scroll_layout.addWidget(basic_info_label)
        
        # Last Name
        self.last_name_edit = LineEdit(self)
        self.last_name_edit.setPlaceholderText("Введите фамилию")
        form_layout.addRow("Фамилия*:", self.last_name_edit)
        
        # First Name
        self.first_name_edit = LineEdit(self)
        self.first_name_edit.setPlaceholderText("Введите имя")
        form_layout.addRow("Имя*:", self.first_name_edit)
        
        # Middle Name
        self.middle_name_edit = LineEdit(self)
        self.middle_name_edit.setPlaceholderText("Введите отчество (при наличии)")
        form_layout.addRow("Отчество:", self.middle_name_edit)
        
        # Phone
        self.phone_edit = LineEdit(self)
        self.phone_edit.setPlaceholderText("Введите телефон (+7XXXXXXXXXX или 8XXXXXXXXXX)")
        form_layout.addRow("Телефон*:", self.phone_edit)
        
        # Email
        self.email_edit = LineEdit(self)
        self.email_edit.setPlaceholderText("Введите email")
        form_layout.addRow("Email*:", self.email_edit)
        
        # Position
        self.position_combo = ComboBox(self)
        self.position_combo.addItems(["Employee", "Manager", "Director"])
        form_layout.addRow("Должность*:", self.position_combo)
        
        # Birth date
        self.birth_date_edit = DateEdit(self)
        self.birth_date_edit.setDate(QDate.currentDate().addYears(-30))  # Default: 30 years ago
        form_layout.addRow("Дата рождения*:", self.birth_date_edit)
        
        # Passport section
        passport_label = StrongBodyLabel("Паспортные данные")
        scroll_layout.addWidget(passport_label)
        scroll_layout.addLayout(form_layout)
        
        # New form layout for passport
        passport_form = QFormLayout()
        passport_form.setVerticalSpacing(10)
        passport_form.setHorizontalSpacing(15)
        
        # Passport series
        self.passport_series_edit = LineEdit(self)
        self.passport_series_edit.setPlaceholderText("Введите серию паспорта (4 цифры)")
        self.passport_series_edit.setMaxLength(4)
        passport_form.addRow("Серия паспорта*:", self.passport_series_edit)
        
        # Passport number
        self.passport_number_edit = LineEdit(self)
        self.passport_number_edit.setPlaceholderText("Введите номер паспорта (6 цифр)")
        self.passport_number_edit.setMaxLength(6)
        passport_form.addRow("Номер паспорта*:", self.passport_number_edit)
        
        scroll_layout.addLayout(passport_form)
        
        # Password section (only for new employees)
        if not self.employee_id:
            password_label = StrongBodyLabel("Учетные данные")
            scroll_layout.addWidget(password_label)
            
            password_form = QFormLayout()
            
            # Password
            self.password_edit = PasswordLineEdit(self)
            self.password_edit.setPlaceholderText("Введите пароль (минимум 6 символов)")
            password_form.addRow("Пароль*:", self.password_edit)
            
            # Confirm password
            self.confirm_password_edit = PasswordLineEdit(self)
            self.confirm_password_edit.setPlaceholderText("Подтвердите пароль")
            password_form.addRow("Подтверждение пароля*:", self.confirm_password_edit)
            
            scroll_layout.addLayout(password_form)
        else:
            # Change password option for existing employees
            password_label = StrongBodyLabel("Сменить пароль (необязательно)")
            scroll_layout.addWidget(password_label)
            
            password_form = QFormLayout()
            
            # Password
            self.password_edit = PasswordLineEdit(self)
            self.password_edit.setPlaceholderText("Введите новый пароль (минимум 6 символов)")
            password_form.addRow("Новый пароль:", self.password_edit)
            
            # Confirm password
            self.confirm_password_edit = PasswordLineEdit(self)
            self.confirm_password_edit.setPlaceholderText("Подтвердите новый пароль")
            password_form.addRow("Подтверждение:", self.confirm_password_edit)
            
            scroll_layout.addLayout(password_form)
        
        # Required fields note
        note_label = CaptionLabel("* - обязательные поля")
        scroll_layout.addWidget(note_label)
        
        # Add scroll area to main layout
        scroll_area = ScrollArea(self)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 10, 0, 0)
        
        # Save button
        self.save_button = PushButton("Сохранить")
        self.save_button.clicked.connect(self.save_employee)
        buttons_layout.addWidget(self.save_button)
        
        # Cancel button
        cancel_button = PushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        layout.addLayout(buttons_layout)
        
    def load_employee_data(self):
        """Load employee data for editing"""
        try:
            db = SessionLocal()
            
            # Get employee
            employee = self.worker_controller.get_by_id(db, self.employee_id)
            if not employee:
                InfoBar.error(
                    title="Ошибка",
                    content="Сотрудник не найден",
                    parent=self
                )
                self.reject()
                return
                
            # Set form values
            self.last_name_edit.setText(employee.last)
            self.first_name_edit.setText(employee.first)
            
            if employee.middle:
                self.middle_name_edit.setText(employee.middle)
                
            if employee.phone:
                self.phone_edit.setText(employee.phone)
                
            if employee.mail:
                self.email_edit.setText(employee.mail)
                
            # Set position
            position_index = self.position_combo.findText(employee.position)
            if position_index >= 0:
                self.position_combo.setCurrentIndex(position_index)
                
            # Set birth date
            if employee.born_date:
                self.birth_date_edit.setDate(employee.born_date.date())
                
            # Set passport data
            if employee.pass_series:
                self.passport_series_edit.setText(employee.pass_series)
                
            if employee.pass_number:
                self.passport_number_edit.setText(employee.pass_number)
                
        except Exception as e:
            InfoBar.error(
                title="Ошибка",
                content=f"Не удалось загрузить данные сотрудника: {str(e)}",
                parent=self
            )
            self.reject()
        finally:
            db.close()
            
    def validate_form(self):
        """Validate form data"""
        # Required fields
        if not self.last_name_edit.text().strip():
            InfoBar.error(
                title="Ошибка",
                content="Фамилия обязательна для заполнения",
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.last_name_edit.setFocus()
            return False
            
        if not self.first_name_edit.text().strip():
            InfoBar.error(
                title="Ошибка",
                content="Имя обязательно для заполнения",
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.first_name_edit.setFocus()
            return False
            
        if not self.phone_edit.text().strip():
            InfoBar.error(
                title="Ошибка",
                content="Телефон обязателен для заполнения",
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.phone_edit.setFocus()
            return False
            
        if not self.email_edit.text().strip():
            InfoBar.error(
                title="Ошибка",
                content="Email обязателен для заполнения",
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.email_edit.setFocus()
            return False
            
        if not self.passport_series_edit.text().strip():
            InfoBar.error(
                title="Ошибка",
                content="Серия паспорта обязательна для заполнения",
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.passport_series_edit.setFocus()
            return False
            
        if not self.passport_number_edit.text().strip():
            InfoBar.error(
                title="Ошибка",
                content="Номер паспорта обязателен для заполнения",
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.passport_number_edit.setFocus()
            return False
            
        # Password required for new employees
        if not self.employee_id and not self.password_edit.text():
            InfoBar.error(
                title="Ошибка",
                content="Пароль обязателен для нового сотрудника",
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.password_edit.setFocus()
            return False
            
        # Validate password match if provided
        if self.password_edit.text() and self.password_edit.text() != self.confirm_password_edit.text():
            InfoBar.error(
                title="Ошибка",
                content="Пароли не совпадают",
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.confirm_password_edit.setFocus()
            return False
            
        # Validate password length if provided
        if self.password_edit.text() and len(self.password_edit.text()) < 6:
            InfoBar.error(
                title="Ошибка",
                content="Пароль должен содержать минимум 6 символов",
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.password_edit.setFocus()
            return False
            
        # Phone format validation
        phone = self.phone_edit.text().strip()
        if not (phone.startswith("+7") and len(phone) == 12) and not (phone.startswith("8") and len(phone) == 11):
            InfoBar.error(
                title="Ошибка",
                content="Телефон должен быть в формате +7XXXXXXXXXX или 8XXXXXXXXXX",
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.phone_edit.setFocus()
            return False
            
        # Email format validation
        email = self.email_edit.text().strip()
        if "@" not in email or "." not in email:
            InfoBar.error(
                title="Ошибка",
                content="Некорректный формат email",
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.email_edit.setFocus()
            return False
            
        # Passport series validation (4 digits)
        passport_series = self.passport_series_edit.text().strip()
        if not passport_series.isdigit() or len(passport_series) != 4:
            InfoBar.error(
                title="Ошибка",
                content="Серия паспорта должна содержать 4 цифры",
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.passport_series_edit.setFocus()
            return False
            
        # Passport number validation (6 digits)
        passport_number = self.passport_number_edit.text().strip()
        if not passport_number.isdigit() or len(passport_number) != 6:
            InfoBar.error(
                title="Ошибка",
                content="Номер паспорта должен содержать 6 цифр",
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.passport_number_edit.setFocus()
            return False
            
        return True
        
    def save_employee(self):
        """Save employee data"""
        if not self.validate_form():
            return
            
        try:
            db = SessionLocal()
            
            # Prepare common data
            first = self.first_name_edit.text().strip()
            last = self.last_name_edit.text().strip()
            middle = self.middle_name_edit.text().strip() or None
            phone = self.phone_edit.text().strip()
            mail = self.email_edit.text().strip()
            position = self.position_combo.currentText()
            born_date = self.birth_date_edit.date().toPyDate()
            pass_series = self.passport_series_edit.text().strip()
            pass_number = self.passport_number_edit.text().strip()
            
            if self.employee_id:
                # Update existing employee
                update_data = WorkerUpdate(
                    first=first,
                    last=last,
                    middle=middle,
                    phone=phone,
                    mail=mail,
                    position=position,
                    born_date=born_date,
                    pass_series=pass_series,
                    pass_number=pass_number
                )
                
                # Add password if provided
                if self.password_edit.text():
                    update_data.password = self.password_edit.text()
                    
                result = self.worker_controller.update(db, self.employee_id, update_data)
                
                if result:
                    InfoBar.success(
                        title="Успех",
                        content="Сотрудник успешно обновлен",
                        parent=self
                    )
                    self.accept()
                else:
                    InfoBar.error(
                        title="Ошибка",
                        content="Не удалось обновить сотрудника",
                        parent=self
                    )
            else:
                # Create new employee
                create_data = WorkerCreate(
                    id=str(uuid.uuid4()),
                    first=first,
                    last=last,
                    middle=middle,
                    phone=phone,
                    mail=mail,
                    position=position,
                    born_date=born_date,
                    pass_series=pass_series,
                    pass_number=pass_number,
                    password=self.password_edit.text()
                )
                
                result = self.worker_controller.create(db, create_data)
                
                if result:
                    InfoBar.success(
                        title="Успех",
                        content="Сотрудник успешно создан",
                        parent=self
                    )
                    self.accept()
                else:
                    InfoBar.error(
                        title="Ошибка",
                        content="Не удалось создать сотрудника",
                        parent=self
                    )
        except Exception as e:
            InfoBar.error(
                title="Ошибка",
                content=f"Не удалось сохранить сотрудника: {str(e)}",
                parent=self
            )
        finally:
            db.close() 