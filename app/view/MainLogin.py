import sys
import re

from PyQt6.QtCore import Qt, QTranslator, QLocale, QRect, pyqtSlot, QSize
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from qfluentwidgets import setThemeColor, FluentTranslator, setTheme, Theme, SplitTitleBar, isDarkTheme, InfoBarIcon, Flyout, PushButton
from qfluentwidgets import BodyLabel, LineEdit, PrimaryPushButton, HyperlinkButton, FluentIcon, TransparentToolButton
from app.view.Ui_LoginWindow import Ui_Form_Registration, Ui_Form_Login, Ui_Form_Info
from qfluentwidgets.components.widgets.stacked_widget import PopUpAniStackedWidget

# Import our resources
try:
    # Try to use Qt resource system
    import app.resource.resource_rc as resource_rc
    BACKGROUND_PATH = ":/images/background.jpg"
    LOGO_PATH = ":/images/logo.png"
except ImportError:
    try:
        # Try relative import
        import resource_rc
        BACKGROUND_PATH = ":/images/background.jpg"
        LOGO_PATH = ":/images/logo.png"
    except ImportError:
        # Fallback to simple file paths
        from app.resource.resource_simple import BACKGROUND_IMG, LOGO_IMG
        BACKGROUND_PATH = BACKGROUND_IMG
        LOGO_PATH = LOGO_IMG

# Import our database and auth controllers
from app.common.db.database import SessionLocal
from app.common.db.controller import AuthController, ClientController, WorkerController
from app.common.db.models_pydantic import LoginRequest, ClientCreate, WorkerCreate
from app.common.signal_bus import signalBus

def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


if isWin11():
    from qframelesswindow import AcrylicWindow as Window
else:
    from qframelesswindow import FramelessWindow as Window


class MainLoginWindow(Window):
    def __init__(self):
        super(MainLoginWindow, self).__init__()
        setTheme(Theme.DARK)
        self.flag = "login"
        self.is_handling_login_atomically = False
        self.last_atomic_login_failure_reason = ""
        
        # Initialize controllers
        self.auth_controller = AuthController()
        self.client_controller = ClientController()
        self.worker_controller = WorkerController()
        
        # To store references to user windows
        self.client_window = None
        self.worker_window = None
        
        # Connect signals
        self._connect_signals()
        
        self.stackedWidget = PopUpAniStackedWidget(self)
        self.stackedWidget.setContentsMargins(0, 0, 0, 0)
        
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        
        self.login = LoginWindow(self)
        self.stackedWidget.addWidget(self.login)
        
        self.registration = RegWindow(self)
        self.stackedWidget.addWidget(self.registration)
        
        self.info = InfoWindow(self)
        self.stackedWidget.addWidget(self.info)
        
        self.verticalLayout.addWidget(self.stackedWidget)
        
        self.login.pushButton_2.clicked.connect(self.switch_widget)
        self.registration.pushButton_2.clicked.connect(self.switch_widget)
        
        # Remove back button from main window
        
        self.login.pushButton.clicked.connect(self.exit_login)
        # self.registration.pushButton.clicked.connect(self.exit_reg)
        self.registration.pushButton.clicked.connect(self.next)
        self.info.pushButton.clicked.connect(self.exit_reg)

        self.setTitleBar(SplitTitleBar(self))
        self.titleBar.raise_()
        self.setWindowTitle('Terra - Ювелирная компания')
        self.setWindowIcon(QIcon(LOGO_PATH))
        
        setThemeColor('#28afe9')
        
        # Allow window resizing
        self.resize(1000, 650)
    
        self.windowEffect.setMicaEffect(self.winId(), isDarkMode=isDarkTheme())
        if not isWin11():
            color = QColor(25, 33, 42) if isDarkTheme() else QColor(240, 244, 249)
            self.setStyleSheet(f"LoginWindow{{background: {color.name()}}}")

        if sys.platform == "darwin":
            self.setSystemTitleBarButtonVisible(True)
            self.titleBar.minBtn.hide()
            self.titleBar.maxBtn.hide()
            self.titleBar.closeBtn.hide()

        self.titleBar.titleLabel.setStyleSheet("""
            QLabel{
                background: transparent;
                font: 13px 'Segoe UI';
                padding: 0 4px;
                color: white
            }
        """)

        # Центрируем окно на экране
        self._center_window()
        
        self._apply_login_theme()
        self.show()
        QApplication.processEvents()

    def _apply_login_theme(self):
        """Applies the specific theme settings for the MainLoginWindow."""
        setTheme(Theme.DARK)
        setThemeColor('#28afe9') # Ensure this is your desired login accent color
        
        # Re-apply window effects and styles that depend on the theme
        self.windowEffect.setMicaEffect(self.winId(), isDarkMode=True) # isDarkTheme() will be true now
        if not isWin11():
            dark_background_color = QColor(25, 33, 42) 
            self.setStyleSheet(f"MainLoginWindow {{background: {dark_background_color.name()}}}\n                                 QWidget {{background-color: transparent;}} \n                                 LoginWindow {{background-color: transparent;}} \n                                 RegWindow {{background-color: transparent;}} \n                                 InfoWindow {{background-color: transparent;}}") # Target MainLoginWindow class name
        else:
            # Ensure background is transparent for Mica effect on Win11+
            self.setStyleSheet(f"MainLoginWindow {{background: transparent;}}\n                                 QWidget {{background-color: transparent;}} \n                                 LoginWindow {{background-color: transparent;}} \n                                 RegWindow {{background-color: transparent;}} \n                                 InfoWindow {{background-color: transparent;}}")

    def _connect_signals(self):
        # Connect SignalBus signals
        signalBus.login_successful.connect(self.on_login_successful)
        signalBus.login_failed.connect(self.on_login_failed)
        signalBus.logout_completed.connect(self._handle_logout_transition)
        
    @pyqtSlot(str, dict)
    def on_login_successful(self, user_type, user_data):
        # Handle successful login
        if user_type == "client":
            from app.view.client.client_window import ClientWindow
            self.client_window = ClientWindow(user_data)
            self.client_window.show()
            self.hide()
        elif user_type == "worker":
            from app.view.worker.worker_window import WorkerWindow
            self.worker_window = WorkerWindow(user_data)
            self.worker_window.show()
            self.hide()
            
    @pyqtSlot(str)
    def on_login_failed(self, reason):
        if hasattr(self, 'is_handling_login_atomically') and self.is_handling_login_atomically:
            self.last_atomic_login_failure_reason = reason
            print(f"Login failure signal received during atomic handling: {reason}")
            return

        # Show login failed message in a flyout
        Flyout.create(
            icon=InfoBarIcon.ERROR,
            title='Ошибка входа',
            content=reason,
            target=self.login.lineEdit_4 if self.stackedWidget.currentIndex() == 0 else self.registration.lineEdit_4,
            parent=self,
            isClosable=True
        )

    @pyqtSlot()
    def _handle_logout_transition(self):
        print("Logout signal received in MainLoginWindow, transitioning to login screen...")
        if self.client_window:
            self.client_window.close()
            self.client_window = None
        
        if self.worker_window:
            self.worker_window.close()
            self.worker_window = None
        
        # Optionally clear login fields
        if hasattr(self, 'login') and self.login:
            if hasattr(self.login, 'lineEdit_3'): # Phone/Username
                self.login.lineEdit_3.clear() 
            if hasattr(self.login, 'lineEdit_4'): # Password
                self.login.lineEdit_4.clear()

        self._apply_login_theme()
        self.show() # Show the login window again

    def systemTitleBarRect(self, size):
        """ Returns the system title bar rect, only works for macOS """
        return QRect(size.width() - 75, 0, 75, size.height())

    def switch_widget(self):
        if self.stackedWidget.currentIndex() == 0:
            self.stackedWidget.setCurrentIndex(1)
        else:
            self.stackedWidget.setCurrentIndex(0)

    def next(self):
        idx = self.stackedWidget.currentIndex() + 1
        
        # Don't try to access nonexistent category field
        
        if self.stackedWidget.currentWidget().enter():
            self.stackedWidget.setCurrentIndex(idx)
        
    def exit_login(self):
        self.flag = "login"
        
        # Получаем и валидируем номер телефона
        phone_input = self.login.lineEdit_3.text().strip()
        self.password = self.login.lineEdit_4.text()
        
        # Очищаем номер от всех символов кроме цифр и +
        cleaned_phone = re.sub(r'[^0-9+]','', phone_input)
        
        # Проверяем формат
        if not (re.match(r'^\+7\d{10}$', cleaned_phone) or 
                re.match(r'^8\d{10}$', cleaned_phone) or
                re.match(r'^\d{10}$', cleaned_phone)):
            Flyout.create(
                icon=InfoBarIcon.ERROR,
                title='Ошибка формата номера',
                content='Телефон должен быть в формате +7XXXXXXXXXX, 8XXXXXXXXXX или XXXXXXXXXX (10 цифр).',
                target=self.login.lineEdit_3,
                parent=self,
                isClosable=True
            )
            return
            
        # Проверяем пароль
        if not self.password:
            Flyout.create(
                icon=InfoBarIcon.ERROR,
                title='Ошибка входа',
                content='Пожалуйста, введите пароль.',
                target=self.login.lineEdit_4,
                parent=self,
                isClosable=True
            )
            return
        
        if self.stackedWidget.currentWidget().enter():
            db = None
            self.is_handling_login_atomically = True
            self.last_atomic_login_failure_reason = ""
            login_succeeded = False
            worker_potentially_exists = True # Assume exists until specific "not found" error
            client_potentially_exists = True # Assume exists until specific "not found" error
            
            try:
                db = SessionLocal()
                
                # Format phone number consistently
                if cleaned_phone.startswith('8'):
                    cleaned_phone = '+7' + cleaned_phone[1:]
                elif len(cleaned_phone) == 10:
                    cleaned_phone = '+7' + cleaned_phone
                
                print(f"Attempting login with phone: {cleaned_phone}")

                # Try worker login
                try:
                    login_data_worker = LoginRequest(
                        phone=cleaned_phone,
                        password=self.password,
                        user_type="worker"
                    )
                    if self.auth_controller.login(db, login_data_worker):
                        login_succeeded = True
                        print("Worker login successful")
                except ValueError as e_worker:
                    # self.last_atomic_login_failure_reason is set by the signal
                    # emitted by AuthController just before this ValueError was raised.
                    expected_worker_not_found_msg = f"Сотрудник с номером телефона {cleaned_phone} не найден"
                    if self.last_atomic_login_failure_reason == expected_worker_not_found_msg:
                        worker_potentially_exists = False
                        print(f"Worker with phone {cleaned_phone} specifically not found (reason: '{self.last_atomic_login_failure_reason}').")
                    else:
                        # This branch would be hit if ValueError is for something other than "not found",
                        # or if the signalled reason was different from the ValueError reason.
                        print(f"Worker login attempt failed (ValueError, signalled reason: '{self.last_atomic_login_failure_reason}', exception: '{str(e_worker)}')")
                except Exception as e_worker_gen:
                    self.last_atomic_login_failure_reason = self.last_atomic_login_failure_reason or "Ошибка при попытке входа как сотрудник."
                    print(f"Worker login attempt failed (General Exception): {str(e_worker_gen)}")

                # If worker login didn't succeed, try client login
                if not login_succeeded:
                    try:
                        login_data_client = LoginRequest(
                            phone=cleaned_phone,
                            password=self.password,
                            user_type="client"
                        )
                        if self.auth_controller.login(db, login_data_client):
                            login_succeeded = True
                            print("Client login successful")
                    except ValueError as e_client:
                        # self.last_atomic_login_failure_reason should now hold the client-related failure reason.
                        expected_client_not_found_msg = f"Клиент с номером телефона {cleaned_phone} не найден"
                        if self.last_atomic_login_failure_reason == expected_client_not_found_msg:
                            client_potentially_exists = False
                            print(f"Client with phone {cleaned_phone} specifically not found (reason: '{self.last_atomic_login_failure_reason}').")
                        else:
                            print(f"Client login attempt failed (ValueError, signalled reason: '{self.last_atomic_login_failure_reason}', exception: '{str(e_client)}')")
                    except Exception as e_client_gen:
                        self.last_atomic_login_failure_reason = self.last_atomic_login_failure_reason or "Ошибка при попытке входа как клиент."
                        print(f"Client login attempt failed (General Exception): {str(e_client_gen)}")
                
                if not login_succeeded:
                    final_error_title = 'Ошибка входа'
                    # Default message if other conditions aren't met
                    final_error_content = 'Не удалось войти. Проверьте логин и пароль.'

                    if not worker_potentially_exists and not client_potentially_exists:
                        final_error_content = "Пользователь с таким номером телефона не существует."
                    elif "Неверный пароль" in self.last_atomic_login_failure_reason:
                        final_error_content = self.last_atomic_login_failure_reason
                    elif self.last_atomic_login_failure_reason: # Use if set by signal and not "Неверный пароль"
                        final_error_content = self.last_atomic_login_failure_reason
                    # If last_atomic_login_failure_reason is empty, the default above is used.
                    
                    Flyout.create(
                        icon=InfoBarIcon.ERROR,
                        title=final_error_title,
                        content=final_error_content,
                        target=self.login.lineEdit_4,
                        parent=self,
                        isClosable=True
                    )

            except Exception as e_outer:
                print(f"Outer authentication process error: {str(e_outer)}")
                Flyout.create(
                    icon=InfoBarIcon.ERROR,
                    title='Критическая ошибка входа',
                    content='Произошла непредвиденная ошибка в процессе входа. Пожалуйста, попробуйте позже.',
                    target=self.login.lineEdit_4,
                    parent=self,
                    isClosable=True
                )
            finally:
                self.is_handling_login_atomically = False
                if db:
                    db.close()
        else: 
            print("Login form validation failed by LoginWindow.enter() method.")
        
    def exit_reg(self):
        self.flag = "reg"
        
        # Проверяем валидацию данных на форме информации
        if not self.info.enter():
            return
        
        self.name = self.info.NameEdit.text()
        self.last = self.info.LastEdit.text()
        self.middle = self.info.MiddleEdit.text() if self.info.MiddleEdit.text().strip() else None
        self.mail = self.info.MailEdit.text() if self.info.MailEdit.text().strip() else None
        
        # Получаем и валидируем номер телефона
        phone_input = self.registration.lineEdit_3.text().strip()
        self.password = self.registration.lineEdit_4.text()
        
        # Очищаем номер от всех символов кроме цифр и +
        cleaned_phone = re.sub(r'[^0-9+]', '', phone_input)
        
        # Проверяем формат
        if not (re.match(r'^\+7\d{10}$', cleaned_phone) or 
                re.match(r'^8\d{10}$', cleaned_phone) or
                re.match(r'^\d{10}$', cleaned_phone)):
            Flyout.create(
                icon=InfoBarIcon.ERROR,
                title='Ошибка формата',
                content='Телефон должен быть в формате +7XXXXXXXXXX, 8XXXXXXXXXX или 10 цифр',
                target=self.registration.lineEdit_3,
                parent=self,
                isClosable=True
            )
            return
            
        # Format phone number consistently using +7 format
        if cleaned_phone.startswith('8'):
            cleaned_phone = '+7' + cleaned_phone[1:]
        elif len(cleaned_phone) == 10:
            cleaned_phone = '+7' + cleaned_phone
            
        print(f"Registering with formatted phone: {cleaned_phone}")
            
        # Проверяем пароль
        if not self.password:
            Flyout.create(
                icon=InfoBarIcon.ERROR,
                title='Ошибка регистрации',
                content='Пожалуйста, введите пароль',
                target=self.registration.lineEdit_4,
                parent=self,
                isClosable=True
            )
            return
        
        # Use proper database session
        db = None
        try:
            db = SessionLocal()
            
            # Проверяем, существует ли уже пользователь с таким телефоном (клиент или работник)
            phone_digits = self.auth_controller.extract_phone_digits(cleaned_phone)
            existing_client = self.client_controller.get_by_phone(db, phone_digits)
            existing_worker = self.worker_controller.get_by_phone(db, phone_digits)
            
            if existing_client or existing_worker:
                Flyout.create(
                    icon=InfoBarIcon.ERROR,
                    title='Ошибка регистрации',
                    content='Пользователь с таким номером телефона уже существует',
                    target=self.registration.lineEdit_3,
                    parent=self,
                    isClosable=True
                )
                return
            
            # Создаем объект для регистрации клиента - обратите внимание, правильное и минимальное использование полей
            client_data = {
                "first": self.name,
                "last": self.last,
                "middle": self.middle,
                "mail": self.mail,
                "phone": cleaned_phone,
                "password": self.password
            }
            
            # Убираем поля со значением None
            client_data = {k: v for k, v in client_data.items() if v is not None}
            
            # Создаем pydantic модель
            client_create = ClientCreate(**client_data)
            
            # Пытаемся создать клиента
            client = self.client_controller.create(db, client_create)
            
            if client:
                # Показываем сообщение об успешной регистрации
                Flyout.create(
                    icon=InfoBarIcon.SUCCESS,
                    title='Успешная регистрация',
                    content='Вы успешно зарегистрировались! Теперь вы можете войти в систему.',
                    target=self.registration.pushButton,
                    parent=self,
                    isClosable=True
                )
                
                # Переключаемся на окно входа
                self.stackedWidget.setCurrentIndex(0)
                
                # Заполняем поля входа данными регистрации для удобства
                self.login.lineEdit_3.setText(phone_input)
                self.login.lineEdit_4.setText(self.password)
            else:
                # Показываем сообщение об ошибке
                Flyout.create(
                    icon=InfoBarIcon.ERROR,
                    title='Ошибка регистрации',
                    content='Не удалось создать учетную запись',
                    target=self.registration.pushButton,
                    parent=self,
                    isClosable=True
                )
        except Exception as e:
            # Показываем детальное сообщение об ошибке
            Flyout.create(
                icon=InfoBarIcon.ERROR,
                title='Ошибка регистрации',
                content=f'Произошла ошибка: {str(e)}',
                target=self.registration.pushButton,
                parent=self,
                isClosable=True
            )
        finally:
            if db:
                db.close()
        
    def _center_window(self):
        """Центрирует окно на экране"""
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)


class RegWindow(QWidget, Ui_Form_Registration):
    """ Registration window """

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setupUi(self)
        # Explicitly set pixmaps after setupUi
        self.label.setPixmap(QPixmap(BACKGROUND_PATH))
        self.label_2.setPixmap(QPixmap(LOGO_PATH))
        self.lineEdit_3.setPlaceholderText('+7...')
        self.lineEdit_4.setPlaceholderText('••••••••••••')
        
        # Remove back button from registration window
        
        # Add password visibility toggle button
        self.toggle_password_button = TransparentToolButton(self.lineEdit_4)
        self.toggle_password_button.setIcon(FluentIcon.VIEW)
        self.toggle_password_button.setIconSize(QSize(16, 16))
        self.toggle_password_button.setFixedSize(24, 24)
        self.toggle_password_button.clicked.connect(self.toggle_password_visibility)
        
        # Style the button properly
        self.toggle_password_button.setStyleSheet("""
            TransparentToolButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            TransparentToolButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        
        # Position the toggle button
        self.update_toggle_button_position()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        pixmap = QPixmap(BACKGROUND_PATH).scaled(
            self.label.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        self.label.setPixmap(pixmap)
        # Update toggle button position when window is resized
        self.update_toggle_button_position()
        
    def update_toggle_button_position(self):
        """Position the toggle button on the left side of the password field"""
        rect = self.lineEdit_4.rect()
        # Размещаем кнопку слева от поля ввода
        self.toggle_password_button.move(10, (rect.height() - 24) // 2)
        # Меняем отступы текста, чтобы он не накладывался на кнопку
        self.lineEdit_4.setTextMargins(36, 0, 10, 0)
        
    def toggle_password_visibility(self):
        """Toggle password visibility between hidden and shown"""
        if self.lineEdit_4.echoMode() == LineEdit.EchoMode.Password:
            self.lineEdit_4.setEchoMode(LineEdit.EchoMode.Normal)
            self.toggle_password_button.setIcon(FluentIcon.HIDE)
        else:
            self.lineEdit_4.setEchoMode(LineEdit.EchoMode.Password)
            self.toggle_password_button.setIcon(FluentIcon.VIEW)

    def enter(self):
        phone_input = self.lineEdit_3.text().strip()
        self.password = self.lineEdit_4.text()
        self.isNumberValid = False
        self.isPasswordValid = False
        
        # Очищаем номер от всех символов кроме цифр и +
        cleaned_phone = re.sub(r'[^0-9+]', '', phone_input)
        
        if not cleaned_phone:
            self.mail_error = Flyout.create(
                icon=InfoBarIcon.WARNING,
                title='Ошибка регистрации!',
                content=self.tr('Введите телефон!'),
                target=self.lineEdit_3,
                parent=self,
                isClosable=True
            )
        else:
            # Проверяем формат
            if re.match(r'^\+7\d{10}$', cleaned_phone) or re.match(r'^8\d{10}$', cleaned_phone):
                # Преобразуем в формат +7XXXXXXXXXX для хранения
                if cleaned_phone.startswith('8'):
                    cleaned_phone = '+7' + cleaned_phone[1:]
                    
                # Для поиска в БД нам нужны последние 10 цифр
                self.number = cleaned_phone
                self.short_phone = cleaned_phone[-10:]
                
                # Проверяем существование как клиента, так и работника
                try:
                    db = SessionLocal()
                    
                    client_controller = ClientController()
                    worker_controller = WorkerController()
                    
                    check_client = client_controller.get_by_phone(db, self.short_phone)
                    check_worker = worker_controller.get_by_phone(db, self.short_phone)
                    
                    if check_client or check_worker:
                        self.mail_error = Flyout.create(
                            icon=InfoBarIcon.ERROR,
                            title='Ошибка регистрации!',
                            content=self.tr('Пользователь с этим номером уже зарегистрирован!'),
                            target=self.lineEdit_3,
                            parent=self,
                            isClosable=True
                        )
                    else:
                        self.isNumberValid = True
                except Exception as e:
                    self.mail_error = Flyout.create(
                        icon=InfoBarIcon.ERROR,
                        title='Ошибка проверки телефона!',
                        content=str(e),
                        target=self.lineEdit_3,
                        parent=self,
                        isClosable=True
                    )
                finally:
                    SessionLocal.remove()
            else:
                self.mail_error = Flyout.create(
                    icon=InfoBarIcon.ERROR,
                    title='Ошибка регистрации!',
                    content=self.tr('Телефон должен быть в формате +7XXXXXXXXXX или 8XXXXXXXXXX'),
                    target=self.lineEdit_3,
                    parent=self,
                    isClosable=True
                )
                
        if not self.password:
            self.password_error = Flyout.create(
                icon=InfoBarIcon.WARNING,
                title='Некорректный пароль!',
                content=self.tr('Введите пароль!'),
                target=self.lineEdit_4,
                parent=self,
                isClosable=True
            )
        else:
            if len(self.password) < 6:
                self.password_error = Flyout.create(
                    icon=InfoBarIcon.WARNING,
                    title='Некорректный пароль!',
                    content=self.tr('Пароль должен содержать не менее 6 символов!'),
                    target=self.lineEdit_4,
                    parent=self,
                    isClosable=True
                )
            elif not bool(re.match(r"^[a-z0-9@_-]+$", self.password)):
                self.password_error = Flyout.create(
                    icon=InfoBarIcon.WARNING,
                    title='Некорректный пароль!',
                    content=self.tr('Пароль может состоять только из латинских букв, цифр и спец. знаков @, _, -, в нижнем регистре!'),
                    target=self.lineEdit_4,
                    parent=self,
                    isClosable=True
                )
            else:
                self.isPasswordValid = True

        return self.isNumberValid and self.isPasswordValid
    
    
class InfoWindow(QWidget, Ui_Form_Info):

    def __init__(self, parent):
        super(InfoWindow, self).__init__(parent)
        self.setupUi(self)
        
        self.parent = parent
        # Add back button to InfoWindow
        self.back_button = PushButton(self)
        self.back_button.setIcon(FluentIcon.LEFT_ARROW)
        self.back_button.setText("Назад")
        self.back_button.setFixedSize(100, 32)
        self.back_button.move(20, 40)
        self.back_button.clicked.connect(self.go_back_to_registration)
        
    def go_back_to_registration(self):
        # Go back to registration screen
        # print("Go back to registration screen")
        if self.parent and hasattr(self.parent, 'stackedWidget'):
            self.parent.stackedWidget.setCurrentIndex(1)

    def enter(self):
        # Получаем данные из полей
        name = self.NameEdit.text().strip()
        last = self.LastEdit.text().strip()
        mail = self.MailEdit.text().strip()
        address = self.AddressEdit.text().strip()
        
        # Валидация имени
        if not name:
            Flyout.create(
                icon=InfoBarIcon.WARNING,
                title='Ошибка регистрации!',
                content=self.tr('Введите имя!'),
                target=self.NameEdit,
                parent=self,
                isClosable=True
            )
            return False
            
        # Проверка формата имени (только буквы и дефис)
        if not re.match(r'^[а-яА-Яёa-zA-Z-]+$', name):
            Flyout.create(
                icon=InfoBarIcon.WARNING,
                title='Ошибка регистрации!',
                content=self.tr('Имя должно содержать только буквы и дефис!'),
                target=self.NameEdit,
                parent=self,
                isClosable=True
            )
            return False
            
        # Валидация фамилии
        if not last:
            Flyout.create(
                icon=InfoBarIcon.WARNING,
                title='Ошибка регистрации!',
                content=self.tr('Введите фамилию!'),
                target=self.LastEdit,
                parent=self,
                isClosable=True
            )
            return False
            
        # Проверка формата фамилии (только буквы и дефис)
        if not re.match(r'^[а-яА-Яёa-zA-Z-]+$', last):
            Flyout.create(
                icon=InfoBarIcon.WARNING,
                title='Ошибка регистрации!',
                content=self.tr('Фамилия должна содержать только буквы и дефис!'),
                target=self.LastEdit,
                parent=self,
                isClosable=True
            )
            return False
            
        # Валидация электронной почты
        if not mail: # Проверяем, что поле не пустое
            Flyout.create(
                icon=InfoBarIcon.WARNING,
                title='Ошибка регистрации!',
                content=self.tr('Введите адрес электронной почты!'),
                target=self.MailEdit,
                parent=self,
                isClosable=True
            )
            return False
        
        # Более строгая проверка email
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', mail):
            Flyout.create(
                icon=InfoBarIcon.WARNING,
                title='Ошибка регистрации!',
                content=self.tr('Некорректный адрес электронной почты!'),
                target=self.MailEdit,
                parent=self,
                isClosable=True
            )
            return False
            
        # Успешная валидация
        return True
    
    
class LoginWindow(QWidget, Ui_Form_Login):
    """ Login window """

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setupUi(self)
        # Explicitly set pixmaps after setupUi
        self.label.setPixmap(QPixmap(BACKGROUND_PATH))
        self.label_2.setPixmap(QPixmap(LOGO_PATH))
        self.lineEdit_3.setPlaceholderText('+7...')
        self.lineEdit_4.setPlaceholderText('••••••••••••')
        # self.label.hide()
        
        # Add password visibility toggle button
        self.toggle_password_button = TransparentToolButton(self.lineEdit_4)
        self.toggle_password_button.setIcon(FluentIcon.VIEW)
        self.toggle_password_button.setIconSize(QSize(16, 16))
        self.toggle_password_button.setFixedSize(24, 24)
        self.toggle_password_button.clicked.connect(self.toggle_password_visibility)
        
        # Style the button properly
        self.toggle_password_button.setStyleSheet("""
            TransparentToolButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            TransparentToolButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        
        # Position the toggle button
        self.update_toggle_button_position()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        pixmap = QPixmap(BACKGROUND_PATH).scaled(
            self.label.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        self.label.setPixmap(pixmap)
        # Update toggle button position when window is resized
        self.update_toggle_button_position()
        
    def update_toggle_button_position(self):
        """Position the toggle button on the left side of the password field"""
        rect = self.lineEdit_4.rect()
        # Размещаем кнопку слева от поля ввода
        self.toggle_password_button.move(10, (rect.height() - 24) // 2)
        # Меняем отступы текста, чтобы он не накладывался на кнопку
        self.lineEdit_4.setTextMargins(36, 0, 10, 0)
        
    def toggle_password_visibility(self):
        """Toggle password visibility between hidden and shown"""
        if self.lineEdit_4.echoMode() == LineEdit.EchoMode.Password:
            self.lineEdit_4.setEchoMode(LineEdit.EchoMode.Normal)
            self.toggle_password_button.setIcon(FluentIcon.HIDE)
        else:
            self.lineEdit_4.setEchoMode(LineEdit.EchoMode.Password)
            self.toggle_password_button.setIcon(FluentIcon.VIEW)

    def enter(self):
        self.number = re.sub(r"[^0-9+]", "", self.lineEdit_3.text())
        self.password = self.lineEdit_4.text()
        self.isNumberValid = False
        self.isPasswordValid = False
        
        if not self.number:
            self.mail_error = Flyout.create(
                icon=InfoBarIcon.WARNING,
                title='Ошибка входа!',
                content=self.tr('Введите телефон!'),
                target=self.lineEdit_3,
                parent=self,
                isClosable=True
            )
            return False
        
        if not self.password:
            self.password_error = Flyout.create(
                icon=InfoBarIcon.WARNING,
                title='Ошибка входа!',
                content=self.tr('Введите пароль!'),
                target=self.lineEdit_4,
                parent=self,
                isClosable=True
            )
            return False
            
        if not bool(re.fullmatch(r"^(?:\+7|8)\d{10}$", self.number)):
            self.mail_error = Flyout.create(
                icon=InfoBarIcon.ERROR,
                title='Ошибка входа!',
                content=self.tr('Некорректный номер телефона!'),
                target=self.lineEdit_3,
                parent=self,
                isClosable=True
            )
            return False
        
        # Basic validation passed
        return True
    
    