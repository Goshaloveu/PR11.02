from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout
from PyQt6.QtGui import QFont

from qfluentwidgets import (
    ScrollArea, LineEdit, PushButton, PrimaryPushButton, 
    PasswordLineEdit, InfoBar, SubtitleLabel, BodyLabel,
    CardWidget, FluentIcon, StrongBodyLabel, ExpandLayout,
    Dialog, MessageBox
)

from ...common.db.models_pydantic import WorkerUpdate
from ...common.db.controller import WorkerController
from ...common.signal_bus import signalBus
import re
from datetime import datetime


class ProfileInterface(ScrollArea):
    def __init__(self, user_data, parent=None):
        super().__init__(parent=parent)
        self.user_data = user_data
        self.worker_controller = WorkerController()
        self.original_email = "" # For email editing consistency if needed later
        self.original_phone = "" # Store original phone for refresh logic
        
        # Create widget and layout
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(20)
        self.scroll_layout.setContentsMargins(30, 30, 30, 30)
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)
        
        # Set up UI
        self._setup_ui()
        self._refresh_displayed_data() # Call to populate and format data initially
        
    def _refresh_displayed_data(self):
        """Обновляет отображаемые данные из user_data и форматирует телефон."""
        self.first_name_input.setText(self.user_data.get('first', ''))
        self.last_name_input.setText(self.user_data.get('last', ''))
        self.middle_name_input.setText(self.user_data.get('middle', '') or "")
        
        raw_phone = self.user_data.get('phone', '')
        self.original_phone = raw_phone # Store original phone
        display_phone = raw_phone
        if raw_phone and len(re.sub(r'[^0-9]', '', raw_phone)) == 10 and not raw_phone.startswith('+'):
            display_phone = f"+7{raw_phone[-10:]}" # Ensure it takes last 10 digits if raw_phone might have other chars
        elif raw_phone and len(re.sub(r'[^0-9]', '', raw_phone)) == 11 and raw_phone.startswith('8'):
            display_phone = f"+7{raw_phone[1:]}"

        self.phone_display.setText(display_phone) # Assuming self.phone_display is now a QLabel

        self.original_email = self.user_data.get('mail', '') # Store original email
        self.email_input.setText(self.original_email)
        
        # For other read-only fields, ensure they are also updated if user_data can change
        position_value = self.user_data.get('position', '')
        self.position_label.setText(position_value if position_value else "Не указано")
        
        hire_date = self.user_data.get('date', '')
        hire_date_text = str(hire_date) if hire_date else "Не указано"
        self.hire_date_label.setText(hire_date_text)
        
        birth_date = self.user_data.get('born_date', '')
        birth_date_text = str(birth_date) if birth_date else "Не указано"
        self.birth_date_label.setText(birth_date_text)

        self.pass_series_input.setText(self.user_data.get('pass_series', ''))
        self.pass_number_input.setText(self.user_data.get('pass_number', ''))

        # Clear password fields if they exist in this interface
        if hasattr(self, 'old_password_input'): self.old_password_input.clear()
        if hasattr(self, 'new_password_input'): self.new_password_input.clear()
        if hasattr(self, 'confirm_password_input'): self.confirm_password_input.clear()

    def _setup_ui(self):
        # Create profile card with improved styling
        self.profile_card = CardWidget(self.scroll_widget)
        profile_layout = QVBoxLayout(self.profile_card)
        profile_layout.setSpacing(20)
        profile_layout.setContentsMargins(25, 25, 25, 25)
        
        # Add title with icon for better visibility
        title_layout = QHBoxLayout()
        profile_icon = QLabel()
        profile_icon.setPixmap(FluentIcon.PEOPLE.icon().pixmap(32, 32))
        title_label = SubtitleLabel("Информация о сотруднике")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_layout.addWidget(profile_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch(1)
        profile_layout.addLayout(title_layout)
        
        # Create form layout with better visual separation
        form_container = QWidget()
        form_container.setStyleSheet("background-color: #f9f9f9; border-radius: 8px;")
        form_layout = QFormLayout(form_container)
        form_layout.setVerticalSpacing(15)  # Increase vertical spacing
        form_layout.setHorizontalSpacing(40)  # Increase horizontal spacing between label and field
        form_layout.setContentsMargins(15, 20, 15, 20)
        
        # Create larger fonts for labels and values
        label_font = QFont("Segoe UI", 12)
        value_font = QFont("Segoe UI", 12)
        
        # Configure form layout to have more spacing
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Create all inputs with improved height and styling
        
        # Phone as read-only QLabel (changed from LineEdit)
        self.phone_display = QLabel(self.profile_card) 
        # self.phone_display.setText(self.user_data.get('phone', '')) # Text set in _refresh_displayed_data
        self.phone_display.setFont(value_font)
        self.phone_display.setMinimumHeight(38) # Keep similar height for alignment
        self.phone_display.setStyleSheet("color: #333; padding: 8px 0px;") # Adjusted padding for QLabel
        # self.phone_input.setReadOnly(True) # Not applicable for QLabel
        # self.phone_input.setStyleSheet("background-color: #f0f0f0;") # Not applicable for QLabel like this
        
        # First name
        self.first_name_input = LineEdit(self.profile_card)
        self.first_name_input.setText(self.user_data.get('first', ''))
        self.first_name_input.setPlaceholderText("Введите имя")
        self.first_name_input.setFont(value_font)
        self.first_name_input.setMinimumHeight(38)
        
        # Last name
        self.last_name_input = LineEdit(self.profile_card)
        self.last_name_input.setText(self.user_data.get('last', ''))
        self.last_name_input.setPlaceholderText("Введите фамилию")
        self.last_name_input.setFont(value_font)
        self.last_name_input.setMinimumHeight(38)
        
        # Middle name
        self.middle_name_input = LineEdit(self.profile_card)
        self.middle_name_input.setText(self.user_data.get('middle', ''))
        self.middle_name_input.setPlaceholderText("Введите отчество")
        self.middle_name_input.setFont(value_font)
        self.middle_name_input.setMinimumHeight(38)
        
        # Email
        self.email_input = LineEdit(self.profile_card)
        self.email_input.setText(self.user_data.get('mail', ''))
        self.email_input.setPlaceholderText("Введите email")
        self.email_input.setFont(value_font)
        self.email_input.setMinimumHeight(38)
        
        # Position (read-only) with improved styling
        position_value = self.user_data.get('position', '')
        self.position_label = QLabel(position_value if position_value else "Не указано")
        self.position_label.setFont(value_font)
        self.position_label.setStyleSheet("color: #444; padding: 8px; background-color: #f0f0f0; border-radius: 4px;")
        
        # Hire date (read-only) with improved styling
        hire_date = self.user_data.get('date', '')
        if hire_date:
            # Format date if needed
            if isinstance(hire_date, str):
                hire_date_text = hire_date
            else:
                hire_date_text = str(hire_date)
        else:
            hire_date_text = "Не указано"
        self.hire_date_label = QLabel(hire_date_text)
        self.hire_date_label.setFont(value_font)
        self.hire_date_label.setStyleSheet("color: #444; padding: 8px; background-color: #f0f0f0; border-radius: 4px;")
            
        # Birth date (read-only) with improved styling
        birth_date = self.user_data.get('born_date', '')
        if birth_date:
            # Format date if needed
            if isinstance(birth_date, str):
                birth_date_text = birth_date
            else:
                birth_date_text = str(birth_date)
        else:
            birth_date_text = "Не указано"
        self.birth_date_label = QLabel(birth_date_text)
        self.birth_date_label.setFont(value_font)
        self.birth_date_label.setStyleSheet("color: #444; padding: 8px; background-color: #f0f0f0; border-radius: 4px;")
            
        # Passport details with better styling
        pass_series = self.user_data.get('pass_series', '')
        pass_number = self.user_data.get('pass_number', '')
        
        # Passport series
        self.pass_series_input = LineEdit(self.profile_card)
        self.pass_series_input.setText(pass_series)
        self.pass_series_input.setPlaceholderText("Серия паспорта")
        self.pass_series_input.setFont(value_font)
        self.pass_series_input.setMinimumHeight(38)
        
        # Passport number
        self.pass_number_input = LineEdit(self.profile_card)
        self.pass_number_input.setText(pass_number)
        self.pass_number_input.setPlaceholderText("Номер паспорта")
        self.pass_number_input.setFont(value_font)
        self.pass_number_input.setMinimumHeight(38)
        
        # Create passport layout with better styling
        passport_layout = QHBoxLayout()
        passport_layout.setSpacing(10)
        passport_layout.addWidget(self.pass_series_input)
        passport_layout.addWidget(QLabel("-"))
        passport_layout.addWidget(self.pass_number_input)
        passport_layout.addStretch()
        
        # Create form row labels with consistent font
        phone_label = QLabel("Телефон (логин):")
        phone_label.setFont(label_font)
        
        first_label = QLabel("Имя:")
        first_label.setFont(label_font)
        
        last_label = QLabel("Фамилия:")
        last_label.setFont(label_font)
        
        middle_label = QLabel("Отчество:")
        middle_label.setFont(label_font)
        
        email_label = QLabel("Email:")
        email_label.setFont(label_font)
        
        position_label = QLabel("Должность:")
        position_label.setFont(label_font)
        
        hire_date_label = QLabel("Дата найма:")
        hire_date_label.setFont(label_font)
        
        birth_date_label = QLabel("Дата рождения:")
        birth_date_label.setFont(label_font)
        
        passport_label = QLabel("Паспорт:")
        passport_label.setFont(label_font)
        
        # Add fields to form layout in logical grouping
        form_layout.addRow(first_label, self.first_name_input)
        form_layout.addRow(last_label, self.last_name_input)
        form_layout.addRow(middle_label, self.middle_name_input)
        
        # Add a spacer for visual separation of groups
        spacer = QWidget()
        spacer.setFixedHeight(10)
        form_layout.addRow("", spacer)
        
        form_layout.addRow(phone_label, self.phone_display) # Changed from self.phone_input
        form_layout.addRow(email_label, self.email_input)
        
        # Add another spacer
        spacer2 = QWidget()
        spacer2.setFixedHeight(10)
        form_layout.addRow("", spacer2)
        
        form_layout.addRow(position_label, self.position_label)
        form_layout.addRow(hire_date_label, self.hire_date_label)
        form_layout.addRow(birth_date_label, self.birth_date_label)
        
        # Add another spacer
        spacer3 = QWidget()
        spacer3.setFixedHeight(10)
        form_layout.addRow("", spacer3)
        
        form_layout.addRow(passport_label, passport_layout)
        
        profile_layout.addWidget(form_container)
        
        # Edit profile button with improved styling
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        self.edit_profile_button = PrimaryPushButton("Обновить профиль")
        self.edit_profile_button.setIcon(FluentIcon.SAVE)
        self.edit_profile_button.clicked.connect(self.update_profile)
        self.edit_profile_button.setFont(QFont("Segoe UI", 12))
        self.edit_profile_button.setMinimumHeight(45)
        self.edit_profile_button.setMinimumWidth(200)
        button_layout.addWidget(self.edit_profile_button)
        
        profile_layout.addLayout(button_layout)
        
        # Add profile card to scroll layout
        self.scroll_layout.addWidget(self.profile_card)
        
        # Create password change card with improved styling
        self.password_card = CardWidget(self.scroll_widget)
        password_layout = QVBoxLayout(self.password_card)
        password_layout.setContentsMargins(25, 25, 25, 25)
        password_layout.setSpacing(20)
        
        # Add title with icon for better visibility
        pass_title_layout = QHBoxLayout()
        pass_icon = QLabel()
        pass_icon.setPixmap(FluentIcon.LINK.icon().pixmap(32, 32))
        password_title = SubtitleLabel("Изменение пароля")
        password_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        pass_title_layout.addWidget(pass_icon)
        pass_title_layout.addWidget(password_title)
        pass_title_layout.addStretch(1)
        password_layout.addLayout(pass_title_layout)
        
        # Create password form with improved styling
        pass_form_container = QWidget()
        pass_form_container.setStyleSheet("background-color: #f9f9f9; border-radius: 8px;")
        pass_form_layout = QFormLayout(pass_form_container)
        pass_form_layout.setVerticalSpacing(15)
        pass_form_layout.setHorizontalSpacing(40)
        pass_form_layout.setContentsMargins(15, 20, 15, 20)
        pass_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Current password
        current_pass_label = QLabel("Текущий пароль:")
        current_pass_label.setFont(label_font)
        self.current_password = PasswordLineEdit(self.password_card)
        self.current_password.setMinimumHeight(38)
        self.current_password.setFont(value_font)
        self.current_password.setPlaceholderText("Введите текущий пароль")
        pass_form_layout.addRow(current_pass_label, self.current_password)
        
        # New password
        new_pass_label = QLabel("Новый пароль:")
        new_pass_label.setFont(label_font)
        self.new_password = PasswordLineEdit(self.password_card)
        self.new_password.setMinimumHeight(38)
        self.new_password.setFont(value_font)
        self.new_password.setPlaceholderText("Введите новый пароль")
        pass_form_layout.addRow(new_pass_label, self.new_password)
        
        # Confirm password
        confirm_pass_label = QLabel("Подтверждение:")
        confirm_pass_label.setFont(label_font)
        self.confirm_password = PasswordLineEdit(self.password_card)
        self.confirm_password.setMinimumHeight(38)
        self.confirm_password.setFont(value_font)
        self.confirm_password.setPlaceholderText("Подтвердите новый пароль")
        pass_form_layout.addRow(confirm_pass_label, self.confirm_password)
        
        # Add password form to layout
        password_layout.addWidget(pass_form_container)
        
        # Change password button with improved styling
        pass_button_layout = QHBoxLayout()
        pass_button_layout.addStretch(1)
        
        self.change_password_button = PrimaryPushButton("Сменить пароль")
        self.change_password_button.setIcon(FluentIcon.LINK)
        self.change_password_button.clicked.connect(self.change_password)
        self.change_password_button.setFont(QFont("Segoe UI", 12))
        self.change_password_button.setMinimumHeight(45)
        self.change_password_button.setMinimumWidth(200)
        pass_button_layout.addWidget(self.change_password_button)
        
        password_layout.addLayout(pass_button_layout)
        
        # Add password card to scroll layout
        self.scroll_layout.addWidget(self.password_card)
        
        # Add note about safety with improved styling
        note_card = CardWidget(self.scroll_widget)
        note_layout = QHBoxLayout(note_card)
        note_layout.setContentsMargins(20, 15, 20, 15)
        
        info_icon = QLabel()
        info_icon.setPixmap(FluentIcon.INFO.icon().pixmap(24, 24))
        note_layout.addWidget(info_icon)
        
        note_text = BodyLabel("Внимание! Никому не сообщайте свой пароль. Используйте надёжные пароли, содержащие буквы разного регистра, цифры и специальные символы.")
        note_text.setWordWrap(True)
        note_layout.addWidget(note_text, 1)
        
        self.scroll_layout.addWidget(note_card)
        
        # Add stretch to push cards to the top
        self.scroll_layout.addStretch(1)
        
    def update_profile(self):
        # Get edited values
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        middle_name = self.middle_name_input.text().strip()
        email = self.email_input.text().strip()
        pass_series = self.pass_series_input.text().strip()
        pass_number = self.pass_number_input.text().strip()
        
        # Simple validation
        if not first_name:
            InfoBar.error(
                title="Ошибка в поле 'Имя'",
                content="Имя не может быть пустым",
                parent=self
            )
            return
            
        if not last_name:
            InfoBar.error(
                title="Ошибка в поле 'Фамилия'",
                content="Фамилия не может быть пустой",
                parent=self
            )
            return
        
        # Validate email
        if email:
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                InfoBar.error(
                    title="Ошибка в поле 'Email'",
                    content="Введите корректный email",
                    parent=self
                )
                return
                
        # Validate passport series (if provided)
        if pass_series:
            if not pass_series.isdigit() or len(pass_series) != 4:
                InfoBar.error(
                    title="Ошибка в поле 'Паспорт'",
                    content="Серия паспорта должна содержать 4 цифры",
                    parent=self
                )
                return
                
        # Validate passport number (if provided)
        if pass_number:
            if not pass_number.isdigit() or len(pass_number) != 6:
                InfoBar.error(
                    title="Ошибка в поле 'Паспорт'",
                    content="Номер паспорта должен содержать 6 цифр",
                    parent=self
                )
                return
        
        # Create update data
        update_data = WorkerUpdate()
        
        # Check changes and update accordingly
        original_first = self.user_data.get('first', '')
        original_last = self.user_data.get('last', '')
        original_middle = self.user_data.get('middle', '')
        original_email = self.user_data.get('mail', '')
        original_pass_series = self.user_data.get('pass_series', '')
        original_pass_number = self.user_data.get('pass_number', '')
        
        if first_name != original_first:
            update_data.first = first_name
            
        if last_name != original_last:
            update_data.last = last_name
            
        if middle_name != original_middle:
            update_data.middle = middle_name
            
        if email != original_email:
            update_data.mail = email
            
        if pass_series != original_pass_series:
            update_data.pass_series = pass_series
            
        if pass_number != original_pass_number:
            update_data.pass_number = pass_number
        
        # Check if there's anything to update
        if (not update_data.first and not update_data.last and not update_data.middle and 
            not update_data.mail and not update_data.pass_series and not update_data.pass_number):
            InfoBar.info(
                title='Нет изменений',
                content='Вы не изменили никаких данных',
                parent=self
            )
            return
            
        # Update profile
        try:
            from ...common.db.database import SessionLocal
            db = SessionLocal()
            worker_id = self.user_data.get('id')
            
            updated_worker = self.worker_controller.update(db, worker_id, update_data)
            
            if updated_worker:
                # Update user_data with new values
                if update_data.first:
                    self.user_data['first'] = update_data.first
                    
                if update_data.last:
                    self.user_data['last'] = update_data.last
                    
                if update_data.middle:
                    self.user_data['middle'] = update_data.middle
                    
                if update_data.mail:
                    self.user_data['mail'] = update_data.mail
                    
                if update_data.pass_series:
                    self.user_data['pass_series'] = update_data.pass_series
                    
                if update_data.pass_number:
                    self.user_data['pass_number'] = update_data.pass_number
                
                # Show success message
                InfoBar.success(
                    title='Профиль обновлен',
                    content='Ваши данные успешно обновлены',
                    parent=self
                )
            else:
                # Show error message
                InfoBar.error(
                    title='Ошибка',
                    content='Не удалось обновить профиль',
                    parent=self
                )
        except Exception as e:
            # Show error message
            InfoBar.error(
                title='Ошибка',
                content=str(e),
                parent=self
            )
        finally:
            db.close()
            
    def change_password(self):
        # Get password values
        old_password = self.current_password.text()
        new_password = self.new_password.text()
        confirm_password = self.confirm_password.text()
        
        # Validate passwords
        if not old_password or not new_password or not confirm_password:
            InfoBar.error(
                title="Ошибка изменения пароля",
                content="Заполните все поля пароля",
                parent=self
            )
            return
            
        if new_password != confirm_password:
            InfoBar.error(
                title="Ошибка изменения пароля",
                content="Пароли не совпадают",
                parent=self
            )
            return
            
        if len(new_password) < 6:
            InfoBar.error(
                title="Ошибка изменения пароля",
                content="Пароль должен быть не менее 6 символов",
                parent=self
            )
            return
            
        # Prepare update data
        try:
            update_data = WorkerUpdate(
                password=new_password
            )
        except Exception as e:
            InfoBar.error(
                title="Ошибка валидации данных",
                content=str(e),
                parent=self
            )
            return
            
        # Update password
        try:
            from ...common.db.database import SessionLocal
            db = SessionLocal()
            
            # Verify old password
            from ...common.db.controller import AuthController
            auth_controller = AuthController()
            
            # Verify old password using phone
            phone = self.user_data.get('phone', '')
            if not phone:
                InfoBar.error(
                    title="Ошибка изменения пароля",
                    content="Не указан телефон для аутентификации",
                    parent=self
                )
                return
                
            if not auth_controller.verify_password(db, phone, old_password, is_employee=True):
                InfoBar.error(
                    title="Ошибка изменения пароля",
                    content="Текущий пароль неверен",
                    parent=self
                )
                return
                
            # Update password
            updated_worker = self.worker_controller.update(db, self.user_data.get('id'), update_data)
            
            if updated_worker:
                # Clear password fields
                self.current_password.clear()
                self.new_password.clear()
                self.confirm_password.clear()
                
                InfoBar.success(
                    title="Пароль изменен",
                    content="Пароль успешно изменен",
                    parent=self
                )
            else:
                InfoBar.error(
                    title="Ошибка изменения пароля",
                    content="Не удалось обновить пароль",
                    parent=self
                )
        except Exception as e:
            InfoBar.error(
                title="Ошибка изменения пароля",
                content=str(e),
                parent=self
            )
        finally:
            if 'db' in locals():
                db.close() 