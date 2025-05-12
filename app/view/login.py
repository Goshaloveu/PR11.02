import sys
import re

from PyQt6.QtCore import Qt, QTranslator, QLocale, QRect
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from qfluentwidgets import setThemeColor, FluentTranslator, setTheme, Theme, SplitTitleBar, isDarkTheme, InfoBarIcon, Flyout
from app.view.Ui_LoginWindow import Ui_Form_Registration, Ui_Form_Login, Ui_Form_Info
from qfluentwidgets.components.widgets.stacked_widget import PopUpAniStackedWidget

from db.models import User
import db.requests as rq


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
        self.type = "Соц. Работник"
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
        
        self.login.pushButton.clicked.connect(self.exit_login)
        # self.registration.pushButton.clicked.connect(self.exit_reg)
        self.registration.pushButton.clicked.connect(self.next)
        self.info.pushButton.clicked.connect(self.exit_reg)

        self.setTitleBar(SplitTitleBar(self))
        self.titleBar.raise_()
        self.setWindowTitle('PyQt-Fluent-Widget')
        self.setWindowIcon(QIcon(":/images/logo.png"))
        
        setThemeColor('#28afe9')
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

        desktop = QApplication.screens()[0].geometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        self.show()
        QApplication.processEvents()


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
        self.type = self.registration.ComboBox.text()
        
        self.info.category.setHidden(self.type == "Соц. Работник")
        
        if self.stackedWidget.currentWidget().enter():
            self.stackedWidget.setCurrentIndex(idx)
        
    def exit_login(self):
        self.flag = "login"
        self.number = re.sub(r"[^0-9]", "", self.login.lineEdit_3.text())[-10:]
        self.password = self.login.lineEdit_4.text()
        
        if self.stackedWidget.currentWidget().enter():
            self.close()
        
    def exit_reg(self):
        self.flag = "reg"
        self.name = self.info.NameEdit.text()
        self.last = self.info.LastEdit.text()
        self.middle = self.info.MiddleEdit.text()
        self.mail = self.info.MailEdit.text()
        self.date = self.info.date.date.toString(Qt.DateFormat.ISODate)
        self.address = self.info.AddressEdit.text()
        self.gender = self.info.gender.text()
        self.category = self.info.category.text()
        
        self.number = self.registration.lineEdit_3.text()[-10:]
        self.password = self.registration.lineEdit_4.text()
        self.type = self.registration.ComboBox.text()
        
        self.close()
        

class RegWindow(QWidget, Ui_Form_Registration):

    def __init__(self, parent):
        super(RegWindow, self).__init__(parent)
        self.setupUi(self)

        self.label.setScaledContents(False)
    
    def resizeEvent(self, e):
        super().resizeEvent(e)
        pixmap = QPixmap(":/images/background.jpg").scaled(
            self.label.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.label.setPixmap(pixmap)

    def enter(self):
        self.mail = self.lineEdit_3.text()
        self.password = self.lineEdit_4.text()
        
        if not self.mail:
            self.mail_error = Flyout.create(
            icon=InfoBarIcon.WARNING,
            title='Ошибка входа!',
            content=self.tr('Введите почту!'),
            target=self.lineEdit_3,
            parent=self,
            isClosable=True
            )

        if not self.password:
            self.password_error = Flyout.create(
            icon=InfoBarIcon.WARNING,
            title='Ошибка входа!',
            content=self.tr('Введите пароль!'),
            target=self.lineEdit_4,
            parent=self,
            isClosable=True
            )
            
        return self.mail and self.password
    
    
class InfoWindow(QWidget, Ui_Form_Info):

    def __init__(self, parent):
        super(InfoWindow, self).__init__(parent)
        self.setupUi(self)

    
class LoginWindow(QWidget, Ui_Form_Login):

    def __init__(self, parent):
        super(LoginWindow, self).__init__(parent)
        self.setupUi(self)

        self.label.setScaledContents(False)
    
    def resizeEvent(self, e):
        super().resizeEvent(e)
        pixmap = QPixmap(":/images/background.jpg").scaled(
            self.label.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.label.setPixmap(pixmap)

    def enter(self):
        self.mail = self.lineEdit_3.text()
        self.password = self.lineEdit_4.text()
        
        if not self.mail:
            self.mail_error = Flyout.create(
            icon=InfoBarIcon.WARNING,
            title='Ошибка входа!',
            content=self.tr('Введите почту!'),
            target=self.lineEdit_3,
            parent=self,
            isClosable=True
            )

        if not self.password:
            self.password_error = Flyout.create(
            icon=InfoBarIcon.WARNING,
            title='Ошибка входа!',
            content=self.tr('Введите пароль!'),
            target=self.lineEdit_4,
            parent=self,
            isClosable=True
            )
            
        return self.mail and self.password
    