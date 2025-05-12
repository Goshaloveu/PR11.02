# main.py
import sys
from typing import Optional
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit, QMessageBox, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import pyqtSlot, Qt
from sqlalchemy.orm import Session # Импортируем Session

from common.db.models_sqlalchemy import Client, Worker

# Настройка логгирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')

# Импорты из нашего проекта
from common.db.database import SessionLocal, init_db # Используем SessionLocal
from common.db.controller import (
    AuthController, ClientController, WorkerController, ProviderController,
    MaterialController, OrderController, MaterialProviderController
)
from common.db.models_pydantic import (
    LoginRequest, ClientCreate, WorkerCreate, ProviderCreate, MaterialCreate,
    OrderCreate, MaterialOnOrderCreate, MaterialProviderCreate, AuthenticatedUser, OrderStatus
)
from common.signal_bus import SignalBus

# --- Главное окно приложения ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ювелирная лавка - Система управления")
        self.setGeometry(100, 100, 800, 600)

        # --- Инициализация ---
        self.auth_controller = AuthController()
        self.client_controller = ClientController()
        self.worker_controller = WorkerController()
        self.provider_controller = ProviderController()
        self.material_controller = MaterialController()
        self.order_controller = OrderController()
        self.mat_prov_controller = MaterialProviderController()

        self.signal_bus = SignalBus()
        self.current_user: Optional[AuthenticatedUser] = None # Храним объект AuthenticatedUser

        # --- UI ---
        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        self._setup_ui() # Выносим создание UI в отдельный метод
        self._connect_signals() # Выносим подключение сигналов

        # --- Начальное состояние UI ---
        self._update_ui_for_logout()

    def _setup_ui(self):
        # --- Секция Входа/Регистрации ---
        self.login_group = QWidget()
        login_layout = QVBoxLayout(self.login_group)
        self.username_input = QLineEdit(placeholderText="Имя пользователя")
        self.password_input = QLineEdit(placeholderText="Пароль", echoMode=QLineEdit.EchoMode.Password)
        self.login_button = QPushButton("Войти")
        # Убрали кнопку регистрации отсюда, т.к. регистрация специфична
        login_layout.addWidget(self.username_input)
        login_layout.addWidget(self.password_input)
        login_layout.addWidget(self.login_button)
        self.layout.addWidget(self.login_group)

        # --- Секция Статуса и Выхода ---
        self.status_group = QWidget(visible=False) # Изначально скрыта
        status_layout = QVBoxLayout(self.status_group)
        self.status_label = QLabel("Статус:")
        self.logout_button = QPushButton("Выйти")
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.logout_button)
        self.layout.addWidget(self.status_group)

        # --- Секция Работы (Пример: Клиенты) ---
        self.work_area = QWidget(visible=False) # Изначально скрыта
        work_layout = QVBoxLayout(self.work_area)
        work_layout.addWidget(QLabel("--- Управление Клиентами ---"))
        self.client_first_input = QLineEdit(placeholderText="Имя")
        self.client_last_input = QLineEdit(placeholderText="Фамилия")
        self.client_user_input = QLineEdit(placeholderText="Логин клиента")
        self.client_pass_input = QLineEdit(placeholderText="Пароль клиента", echoMode=QLineEdit.EchoMode.Password)
        self.add_client_button = QPushButton("Добавить клиента")
        self.clients_table = QTableWidget(columnCount=4) # ID, Имя, Фамилия, Логин
        self.clients_table.setHorizontalHeaderLabels(["ID", "Имя", "Фамилия", "Логин"])
        self.clients_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.refresh_clients_button = QPushButton("Обновить список клиентов")

        client_form_layout = QVBoxLayout()
        client_form_layout.addWidget(self.client_first_input)
        client_form_layout.addWidget(self.client_last_input)
        client_form_layout.addWidget(self.client_user_input)
        client_form_layout.addWidget(self.client_pass_input)
        client_form_layout.addWidget(self.add_client_button)
        work_layout.addLayout(client_form_layout)
        work_layout.addWidget(self.refresh_clients_button)
        work_layout.addWidget(self.clients_table)

        self.layout.addWidget(self.work_area)

        # --- Метка для общей информации/ошибок ---
        self.info_label = QLabel("")
        self.layout.addWidget(self.info_label)
        self.layout.addStretch() # Добавляем растяжение вниз

    def _connect_signals(self):
        # Кнопки UI
        self.login_button.clicked.connect(self.handle_login)
        self.logout_button.clicked.connect(self.handle_logout)
        self.add_client_button.clicked.connect(self.handle_add_client)
        self.refresh_clients_button.clicked.connect(self.handle_refresh_clients)

        # SignalBus
        self.signal_bus.login_successful.connect(self.on_login_successful)
        self.signal_bus.login_failed.connect(self.on_login_failed)
        self.signal_bus.logout_completed.connect(self.on_logout_completed)
        self.signal_bus.database_error.connect(self.show_db_error)
        self.signal_bus.client_created.connect(self.on_client_created)
        # Добавить обработчики для других сигналов...

    # --- Методы управления UI ---
    def _update_ui_for_login(self):
        self.login_group.setVisible(False)
        self.status_group.setVisible(True)
        self.work_area.setVisible(True) # Показываем рабочую область
        # Очищаем поля ввода логина/пароля
        self.username_input.clear()
        self.password_input.clear()

    def _update_ui_for_logout(self):
        self.login_group.setVisible(True)
        self.status_group.setVisible(False)
        self.work_area.setVisible(False) # Скрываем рабочую область
        self.current_user = None
        self.status_label.setText("Статус: Не авторизован")
        self.clients_table.setRowCount(0) # Очищаем таблицу
        self.info_label.clear()

    # --- Общая функция для выполнения действий с БД ---
    def _execute_db_action(self, action, *args, success_msg=None, failure_msg="Ошибка выполнения операции"):
        """ Выполняет действие с БД в сессии """
        # ВАЖНО: В реальном GUI приложении длительные операции
        # нужно выносить в фоновые потоки (QThread, QThreadPool),
        # чтобы не блокировать интерфейс. Этот пример упрощен.
        db: Optional[Session] = None
        result = None
        try:
            db = SessionLocal() # Новая сессия для действия
            result = action(db, *args)
            # Коммит/роллбэк делается внутри методов репозитория
            if success_msg: self.info_label.setText(success_msg)
            return result # Возвращаем результат действия
        except ValueError as ve: # Ловим ожидаемые ошибки валидации
             logging.warning(f"Action Error: {ve}")
             self.show_db_error(f"{failure_msg}: {ve}")
        except Exception as e:
            logging.exception("Unhandled exception during DB action:") # Логируем с traceback
            self.show_db_error(f"Непредвиденная ошибка: {e}")
        finally:
            if db: SessionLocal.remove() # Закрываем сессию
        return None # Возвращаем None при ошибке

    # --- Слоты для обработки действий пользователя ---
    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            self.show_db_error("Введите имя пользователя и пароль.")
            return

        login_data = LoginRequest(username=username, password=password)
        self.info_label.setText(f"Попытка входа для {username}...")
        # Сервис сам отправит сигнал login_successful или login_failed
        self._execute_db_action(
            self.auth_controller.login,
            login_data,
            failure_msg="Ошибка входа"
        )
        # Результат обработается в on_login_successful / on_login_failed

    def handle_logout(self):
        self.auth_controller.logout() # Отправит сигнал logout_completed

    def handle_add_client(self):
        first = self.client_first_input.text().strip()
        last = self.client_last_input.text().strip()
        username = self.client_user_input.text().strip()
        password = self.client_pass_input.text().strip()

        # --- Валидация на стороне UI (базовая) ---
        if not all([first, last, username, password]):
            self.show_db_error("Заполните все поля для добавления клиента.")
            return
        if len(password) < 6:
            self.show_db_error("Пароль клиента должен быть не менее 6 символов.")
            return

        try:
            client_data = ClientCreate(first=first, last=last, username=username, password=password)
        except Exception as e: # Ловим ошибки валидации Pydantic
             self.show_db_error(f"Ошибка данных клиента: {e}")
             return

        self.info_label.setText(f"Добавление клиента {username}...")
        # Сигнал client_created будет отправлен из сервиса
        new_client = self._execute_db_action(
            self.client_controller.create,
            client_data,
            failure_msg="Ошибка добавления клиента"
            # Сообщение об успехе будет в on_client_created
        )
        if new_client: # Если операция прошла успешно (не было исключений)
             self.client_first_input.clear()
             self.client_last_input.clear()
             self.client_user_input.clear()
             self.client_pass_input.clear()
             # Обновляем таблицу
             self.handle_refresh_clients()


    def handle_refresh_clients(self):
        self.info_label.setText("Загрузка списка клиентов...")
        clients = self._execute_db_action(
            self.client_controller.get_all,
            limit=1000, # Получаем больше клиентов для примера
            success_msg="Список клиентов обновлен.",
            failure_msg="Ошибка загрузки клиентов"
        )
        if clients is not None: # Проверяем, что действие не вернуло None из-за ошибки
            self.clients_table.setRowCount(len(clients))
            for row, client in enumerate(clients):
                # Используем alias id_ для доступа к ID из Pydantic модели
                self.clients_table.setItem(row, 0, QTableWidgetItem(client.id_))
                self.clients_table.setItem(row, 1, QTableWidgetItem(client.first))
                self.clients_table.setItem(row, 2, QTableWidgetItem(client.last))
                self.clients_table.setItem(row, 3, QTableWidgetItem(client.username))
                # Запрещаем редактирование ячеек
                for col in range(4):
                    item = self.clients_table.item(row, col)
                    if item: item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        else:
             self.clients_table.setRowCount(0) # Очищаем при ошибке


    # --- Слоты для обработки сигналов SignalBus ---
    @pyqtSlot(str, dict)
    def on_login_successful(self, user_type: str, user_data: dict):
        # Преобразуем dict обратно в Pydantic модель (если нужно)
        if user_type == 'client':
             user_model = Client(**user_data)
        elif user_type == 'worker':
             user_model = Worker(**user_data)
        else:
             user_model = None # Неизвестный тип

        self.current_user = AuthenticatedUser(user_type=user_type, user_data=user_model)
        username = getattr(user_model, 'username', 'N/A')
        self.status_label.setText(f"Статус: Авторизован как {username} (Тип: {user_type})")
        self._update_ui_for_login()
        self.info_label.setText(f"Добро пожаловать, {username}!")
        # Загружаем данные, релевантные для пользователя
        if user_type == 'client' or user_type == 'worker': # Примерно одинаковый доступ пока
            self.handle_refresh_clients() # Обновляем клиентов при входе

    @pyqtSlot(str)
    def on_login_failed(self, reason: str):
        self.show_db_error(f"Ошибка входа: {reason}")
        self.info_label.setText("Ошибка входа.")
        # UI не меняем, остаемся на экране логина

    @pyqtSlot()
    def on_logout_completed(self):
        self._update_ui_for_logout()

    @pyqtSlot(str)
    def show_db_error(self, message: str):
        # Устанавливаем фокус, чтобы было видно
        self.info_label.setText(f"Ошибка: {message}")
        QMessageBox.warning(self, "Ошибка", message)

    @pyqtSlot(dict)
    def on_client_created(self, client_info: dict):
        # Вызывается ПОСЛЕ успешного добавления клиента в БД и коммита
        name = f"{client_info.get('first', '')} {client_info.get('last', '')}"
        self.info_label.setText(f"Клиент '{name}' успешно добавлен.")
        # Обновляем таблицу клиентов, чтобы увидеть нового
        self.handle_refresh_clients()


# --- Точка входа ---
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # --- Проверка подключения к БД ---
    try:
        db = SessionLocal()
        db.connection() # Простая проверка соединения
        logging.info("Database connection successful on startup.")
        SessionLocal.remove()
    except Exception as e:
        logging.error(f"CRITICAL: Failed to connect to the database on startup: {e}")
        QMessageBox.critical(None, "Ошибка подключения к БД", f"Не удалось подключиться к базе данных:\n{e}\n\nПроверьте настройки в config.py и состояние сервера MySQL.")
        sys.exit(1)

    # --- Запуск приложения ---
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())