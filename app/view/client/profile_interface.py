from PyQt6.QtCore import Qt, pyqtSlot, QEvent
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout, QSizePolicy
from PyQt6.QtGui import QFont

from qfluentwidgets import (
    ScrollArea, LineEdit, PushButton, PrimaryPushButton, 
    PasswordLineEdit, InfoBar, SubtitleLabel, BodyLabel,
    CardWidget, FluentIcon, StrongBodyLabel, ExpandLayout,
    Dialog, MessageBox, TitleLabel, InfoBarPosition, setTheme, Theme
)

from ...common.db.models_pydantic import ClientUpdate
from ...common.db.controller import ClientController
from ...common.signal_bus import signalBus
import re


class ProfileInterface(ScrollArea):
    def __init__(self, user_data, parent=None):
        super().__init__(parent=parent)
        self.user_data = user_data
        self.client_controller = ClientController()
        self.original_phone = ""
        self.original_email = ""
        
        # Установка objectName для интерфейса
        self.setObjectName("profileInterface")
        
        # Create widget and layout
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(28)
        self.scroll_layout.setContentsMargins(30, 30, 30, 30)
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)
        
        # Set modern fonts as class variables
        self.main_font = QFont("Segoe UI", 11)
        self.header_font = QFont("Segoe UI", 16, weight=QFont.Weight.DemiBold)
        self.section_font = QFont("Segoe UI", 14, weight=QFont.Weight.Medium)
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
            #profileInterface {
                background-color: transparent;
            }
            
            /* Additional styling for dark theme compatibility */
            .QDarkTheme CardWidget {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
            }
            
            .QDarkTheme #avatar_frame {
                background-color: #3D3D3D;
                border: 2px solid #4D4D4D;
            }
        """)
        
        # Install event filter to detect when interface becomes visible
        self.installEventFilter(self)
        
        # Set up UI
        self._setup_ui()
        
    def eventFilter(self, obj, event):
        # When this widget becomes visible, refresh the displayed data
        if event.type() == QEvent.Type.ShowToParent:
            # Make sure the UI has been set up before refreshing
            if hasattr(self, 'first_name_input') and hasattr(self, 'phone_display'):
                self._refresh_displayed_data()
        return super().eventFilter(obj, event)
    
    def _refresh_displayed_data(self):
        """Обновляет отображаемые данные из user_data и сбрасывает состояние полей"""
        # Save original values
        raw_phone = self.user_data.get('phone', '')
        self.original_phone = raw_phone
        self.original_email = self.user_data.get('mail', '')
        
        # Update form fields
        self.first_name_input.setText(self.user_data.get('first', ''))
        self.last_name_input.setText(self.user_data.get('last', ''))
        self.middle_name_input.setText(self.user_data.get('middle', '') or "")
        
        # Format phone for display (add +7 prefix for 10-digit numbers)
        display_phone = raw_phone
        if raw_phone and len(re.sub(r'[^0-9]', '', raw_phone)) == 10:
            display_phone = f"+7{raw_phone}"
        
        self.phone_display.setText(display_phone)
        self.email_input.setText(self.original_email)
        
        # Clear password fields
        self.old_password_input.clear()
        self.new_password_input.clear()
        self.confirm_password_input.clear()
        
    def _setup_ui(self):
        # Add user name header with elegant styling
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)
        
        # Subtle separator line
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        separator.setStyleSheet("background-color: #dcdcdc; margin: 10px 0px 20px 0px;")
        header_layout.addWidget(separator)
        
        self.scroll_layout.addLayout(header_layout)
        
        # Create profile card with improved styling
        self.profile_card = CardWidget(self.scroll_widget)
        self.profile_card.setStyleSheet("""
            CardWidget {
                border-radius: 10px;
            }
        """)
        profile_layout = QVBoxLayout(self.profile_card)
        profile_layout.setContentsMargins(24, 24, 24, 24)
        profile_layout.setSpacing(20)
        
        # Add title with icon - improved styling
        title_layout = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(FluentIcon.PEOPLE.icon().pixmap(28, 28))
        title_label = SubtitleLabel("Личная информация")
        title_label.setFont(self.section_font)
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch(1)
        profile_layout.addLayout(title_layout)
        
        # Create form layout for info - improved spacing
        form_layout = QFormLayout()
        form_layout.setSpacing(16)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setHorizontalSpacing(20)
        form_layout.setVerticalSpacing(16)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Custom styled labels for field names
        field_label_style = "color: #555; font-weight: 600; font-size: 11pt;"
        field_value_style = "font-size: 11pt;"
        
        # Phone as read-only label with improved styling
        self.phone_display = QLabel(self.profile_card)
        self.phone_display.setText(self.user_data.get('phone', ''))
        self.phone_display.setStyleSheet(field_value_style)
        self.original_phone = self.user_data.get('phone', '')
        
        self.email_input = LineEdit(self.profile_card)
        self.email_input.setText(self.user_data.get('mail', ''))
        self.email_input.setPlaceholderText("Введите email")
        self.email_input.setMinimumWidth(250)
        self.email_input.setFont(self.main_font)
        self.original_email = self.user_data.get('mail', '')
        
        # First name, last name and middle name - make editable fields
        self.first_name_input = LineEdit(self.profile_card)
        self.first_name_input.setText(self.user_data.get('first', ''))
        self.first_name_input.setPlaceholderText("Введите имя")
        self.first_name_input.setFont(self.main_font)
        
        self.last_name_input = LineEdit(self.profile_card)
        self.last_name_input.setText(self.user_data.get('last', ''))
        self.last_name_input.setPlaceholderText("Введите фамилию")
        self.last_name_input.setFont(self.main_font)
        
        self.middle_name_input = LineEdit(self.profile_card)
        self.middle_name_input.setText(self.user_data.get('middle', '') or "")
        self.middle_name_input.setPlaceholderText("Введите отчество (при наличии)")
        self.middle_name_input.setFont(self.main_font)
        
        # Registration date
        registration_date = self.user_data.get('date', '')
        if registration_date:
            # Format date if needed
            if isinstance(registration_date, str):
                self.registration_date_label = QLabel(registration_date)
            else:
                self.registration_date_label = QLabel(str(registration_date))
        else:
            self.registration_date_label = QLabel("Не указано")
        
        # Style labels
        self.registration_date_label.setStyleSheet(field_value_style)
            
        # Create styled field labels
        name_label = StrongBodyLabel("Имя:")
        name_label.setStyleSheet(field_label_style)
        
        last_label = StrongBodyLabel("Фамилия:")
        last_label.setStyleSheet(field_label_style)
        
        middle_label = StrongBodyLabel("Отчество:")
        middle_label.setStyleSheet(field_label_style)
        
        phone_label = StrongBodyLabel("Телефон (логин):")
        phone_label.setStyleSheet(field_label_style)
        
        email_label = StrongBodyLabel("Email:")
        email_label.setStyleSheet(field_label_style)
        
        date_label = StrongBodyLabel("Дата регистрации:")
        date_label.setStyleSheet(field_label_style)
        
        # Add fields to form layout
        form_layout.addRow(name_label, self.first_name_input)
        form_layout.addRow(last_label, self.last_name_input)
        form_layout.addRow(middle_label, self.middle_name_input)
        form_layout.addRow(phone_label, self.phone_display)
        form_layout.addRow(email_label, self.email_input)
        form_layout.addRow(date_label, self.registration_date_label)
        
        profile_layout.addLayout(form_layout)
        
        # Edit profile button
        self.edit_profile_button = PrimaryPushButton("Обновить профиль")
        self.edit_profile_button.clicked.connect(self.update_profile)
        self.edit_profile_button.setFont(self.main_font)
        profile_layout.addWidget(self.edit_profile_button)
        
        # Add profile card to scroll layout
        self.scroll_layout.addWidget(self.profile_card)
        
        # Create password change card
        self.password_card = CardWidget(self.scroll_widget)
        self.password_card.setStyleSheet("""
            CardWidget {
                border-radius: 10px;
            }
        """)
        password_layout = QVBoxLayout(self.password_card)
        password_layout.setContentsMargins(24, 24, 24, 24)
        password_layout.setSpacing(20)
        
        # Add title with icon
        password_title_layout = QHBoxLayout()
        password_icon = QLabel()
        password_icon.setPixmap(FluentIcon.SEND_FILL.icon().pixmap(28, 28))
        password_title = SubtitleLabel("Изменение пароля")
        password_title.setFont(self.section_font)
        
        password_title_layout.addWidget(password_icon)
        password_title_layout.addWidget(password_title)
        password_title_layout.addStretch(1)
        password_layout.addLayout(password_title_layout)
        
        # Create password form with improved spacing
        password_form = QFormLayout()
        password_form.setSpacing(16)
        password_form.setVerticalSpacing(16)
        
        # Add password fields
        self.old_password_input = PasswordLineEdit(self.password_card)
        self.old_password_input.setPlaceholderText("Введите текущий пароль")
        self.old_password_input.setMinimumWidth(250)
        self.old_password_input.setFont(self.main_font)
        
        self.new_password_input = PasswordLineEdit(self.password_card)
        self.new_password_input.setPlaceholderText("Введите новый пароль")
        self.new_password_input.setMinimumWidth(250)
        self.new_password_input.setFont(self.main_font)
        
        self.confirm_password_input = PasswordLineEdit(self.password_card)
        self.confirm_password_input.setPlaceholderText("Подтвердите новый пароль")
        self.confirm_password_input.setMinimumWidth(250)
        self.confirm_password_input.setFont(self.main_font)
        
        # Create styled password field labels
        old_password_label = StrongBodyLabel("Текущий пароль:")
        old_password_label.setStyleSheet(field_label_style)
        
        new_password_label = StrongBodyLabel("Новый пароль:")
        new_password_label.setStyleSheet(field_label_style)
        
        confirm_password_label = StrongBodyLabel("Подтверждение:")
        confirm_password_label.setStyleSheet(field_label_style)
        
        # Add fields to form layout
        password_form.addRow(old_password_label, self.old_password_input)
        password_form.addRow(new_password_label, self.new_password_input)
        password_form.addRow(confirm_password_label, self.confirm_password_input)
        
        password_layout.addLayout(password_form)
        
        # Change password button
        self.change_password_button = PrimaryPushButton("Изменить пароль")
        self.change_password_button.clicked.connect(self.change_password)
        self.change_password_button.setFont(self.main_font)
        password_layout.addWidget(self.change_password_button)
        
        # Add password card to scroll layout
        self.scroll_layout.addWidget(self.password_card)
        
        # Add stretch to push cards to the top
        self.scroll_layout.addStretch(1)
        
        # Инициируем отображение данных
        self._refresh_displayed_data()
        
    def _clear_password_fields(self):
        """Очищает поля ввода пароля"""
        self.old_password_input.clear()
        self.new_password_input.clear()
        self.confirm_password_input.clear()
        
    def update_profile(self):
        # Get edited values (phone is now read-only)
        edited_email = self.email_input.text().strip()
        edited_first_name = self.first_name_input.text().strip()
        edited_last_name = self.last_name_input.text().strip()
        edited_middle_name = self.middle_name_input.text().strip()
        
        # Validate inputs
        if not edited_first_name:
            InfoBar.error(
                title="Ошибка в поле 'Имя'",
                content="Имя не может быть пустым",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
            
        if not edited_last_name:
            InfoBar.error(
                title="Ошибка в поле 'Фамилия'",
                content="Фамилия не может быть пустой",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
            
        # Validate email
        if edited_email:
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, edited_email):
                InfoBar.error(
                    title="Ошибка в поле 'Email'",
                    content="Введите корректный email",
                    parent=self,
                    position=InfoBarPosition.TOP
                )
                return
        
        # Create update data - only include fields that changed
        update_data = ClientUpdate()
        
        # Check each field for changes
        original_first = self.user_data.get('first', '')
        original_last = self.user_data.get('last', '')
        original_middle = self.user_data.get('middle', '')
        
        if edited_first_name != original_first:
            update_data.first = edited_first_name
            
        if edited_last_name != original_last:
            update_data.last = edited_last_name
            
        if edited_middle_name != original_middle:
            update_data.middle = edited_middle_name
            
        if edited_email != self.original_email:
            update_data.mail = edited_email
            
        # Check if there's anything to update
        if not update_data.first and not update_data.last and not update_data.middle and not update_data.mail:
            InfoBar.info(
                title='Нет изменений',
                content='Вы не изменили никаких данных',
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
            
        # Update profile
        try:
            from ...common.db.database import SessionLocal
            db = SessionLocal()
            client_id = self.user_data.get('id')
            
            updated_client = self.client_controller.update(db, client_id, update_data)
            
            if updated_client:
                # Update user_data with new values
                if update_data.first:
                    self.user_data['first'] = update_data.first
                    
                if update_data.last:
                    self.user_data['last'] = update_data.last
                    
                if update_data.middle:
                    self.user_data['middle'] = update_data.middle
                    
                if update_data.mail:
                    self.user_data['mail'] = update_data.mail
                
                # Show success message
                InfoBar.success(
                    title='Профиль обновлен',
                    content='Ваши данные успешно обновлены',
                    parent=self,
                    position=InfoBarPosition.TOP
                )
                
                # Refresh displayed data
                self._refresh_displayed_data()
            else:
                # Show error message
                InfoBar.error(
                    title='Ошибка',
                    content='Не удалось обновить профиль',
                    parent=self,
                    position=InfoBarPosition.TOP
                )
        except Exception as e:
            # Show error message
            InfoBar.error(
                title='Ошибка',
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP
            )
        finally:
            if 'db' in locals():
                db.close()
        
    def change_password(self):
        # Get password values
        old_password = self.old_password_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()
        
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
            update_data = ClientUpdate(
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
                
            if not auth_controller.verify_password(db, phone, old_password, is_employee=False):
                InfoBar.error(
                    title="Ошибка изменения пароля",
                    content="Текущий пароль неверен",
                    parent=self
                )
                return
                
            # Update password
            updated_client = self.client_controller.update(db, self.user_data.get('id'), update_data)
            
            if updated_client:
                # Clear password fields
                self._clear_password_fields()
                
                # Show success message with animation
                InfoBar.success(
                    title="Пароль изменен",
                    content="Пароль успешно изменен. Теперь вы можете использовать новый пароль для входа.",
                    parent=self,
                    duration=5000,
                    position=InfoBarPosition.TOP
                )
            else:
                # Show error message
                InfoBar.error(
                    title='Ошибка обновления',
                    content='Не удалось обновить профиль',
                    orient=Qt.Orientation.Vertical,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self
                )
        except Exception as e:
            InfoBar.error(
                title="Ошибка изменения пароля",
                content=str(e),
                parent=self
            )
        finally:
            SessionLocal.remove() 