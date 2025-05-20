from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QListWidgetItem, QFrame, QTreeWidgetItem, QHBoxLayout,
                             QTreeWidgetItemIterator, QTableWidgetItem)
from qfluentwidgets import TreeWidget, TableWidget, ListWidget, HorizontalFlipView, TitleLabel
from .legacy.gallery_interface import GalleryInterface
from ..common.translator import Translator
from ..common.style_sheet import StyleSheet
from PyQt6 import QtWidgets

from PyQt6.QtCore import Qt, QUrl, QEvent, QPoint, QModelIndex
from PyQt6.QtGui import QDesktopServices, QPainter, QPen, QColor
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame

from qfluentwidgets import (ScrollArea, PushButton, ToolButton, FluentIcon, ComboBox,
                            isDarkTheme, IconWidget, Theme, ToolTipFilter, TitleLabel, CaptionLabel,
                            StrongBodyLabel, BodyLabel, CardWidget, TransparentToolButton, toggleTheme)
from app.view import message_winodws as mess
# from ..common.config import cfg, FEEDBACK_URL, HELP_URL, EXAMPLE_URLsss
from ..common.icon import Icon
from ..common.style_sheet import StyleSheet
from ..common.signal_bus import signalBus
import db.requests as rq

class SeparatorWidget(QWidget):
    """ Seperator widget """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(6, 16)

    def paintEvent(self, e):
        painter = QPainter(self)
        pen = QPen(1)
        pen.setCosmetic(True)
        c = QColor(255, 255, 255, 21) if isDarkTheme() else QColor(0, 0, 0, 15)
        pen.setColor(c)
        painter.setPen(pen)

        x = self.width() // 2
        painter.drawLine(x, 0, x, self.height())
        

class ToolBar(QWidget):
    """ Tool bar """

    def __init__(self, title, subtitle, parent=None):
        super().__init__(parent=parent)
        self.titleLabel = TitleLabel(title, self)
        self.subtitleLabel = CaptionLabel(subtitle, self)

        self.addButton = PushButton(
            self.tr('Добавить задание'), self, FluentIcon.ADD)
        
        self.ComboBoxType = ComboBox(self)
        self.ComboBoxType.addItems(["В работе", "Выполнено", "Отменено"])
        # self.deleteButton = PushButton(self.tr('Удалить запись'), self, FluentIcon.DELETE)
        # self.updateButton = PushButton(self.tr("Обновить запись"), self, FluentIcon.UPDATE)
        # self.separator = SeparatorWidget(self)
        # self.another_sep = SeparatorWidget(self)

        self.vBoxLayout = QVBoxLayout(self)
        self.buttonLayout = QHBoxLayout()

        self.__initWidget()

    def __initWidget(self):
        self.setFixedHeight(138)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 22, 36, 12)
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(4)
        self.vBoxLayout.addWidget(self.subtitleLabel)
        self.vBoxLayout.addSpacing(4)
        self.vBoxLayout.addLayout(self.buttonLayout, 1)
        self.vBoxLayout.setAlignment(Qt.AlignTop)

        self.buttonLayout.setSpacing(4)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.addWidget(self.addButton, 0, Qt.AlignLeft)
        self.buttonLayout.addWidget(self.ComboBoxType, 0, Qt.AlignmentFlag.AlignRight)
        # self.buttonLayout.addWidget(self.another_sep, 0, Qt.AlignRight)
        # self.buttonLayout.addWidget(self.deleteButton, 0, Qt.AlignRight)
        # self.buttonLayout.addWidget(self.separator, 0, Qt.AlignRight)
        # self.buttonLayout.addWidget(self.updateButton, 0, Qt.AlignRight)
        self.buttonLayout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.addButton.installEventFilter(ToolTipFilter(self.addButton))
        self.ComboBoxType.installEventFilter(ToolTipFilter(self.ComboBoxType))
        # self.deleteButton.installEventFilter(ToolTipFilter(self.deleteButton))
        # self.updateButton.installEventFilter(
            # ToolTipFilter(self.updateButton))
        self.addButton.setToolTip(self.tr('Добавляет запись в таблицу'))
        self.ComboBoxType.setToolTip(self.tr('Добавляет фильтр записей по статусу'))
        # self.deleteButton.setToolTip(self.tr('Удаляет запись из таблицы'))
        # self.updateButton.setToolTip(self.tr('Обновляет запись в таблице'))

        # self.addButton.clicked.connect(lambda: toggleTheme(True))
        # self.updateButton.clicked.connect(signalBus.supportSignal)

        self.subtitleLabel.setTextColor(QColor(96, 96, 96), QColor(216, 216, 216))

class ToolBarOwner(QWidget):
    """ Tool bar """

    def __init__(self, title, subtitle, parent=None):
        super().__init__(parent=parent)
        self.titleLabel = TitleLabel(title, self)
        self.subtitleLabel = CaptionLabel(subtitle, self)

        # self.addButton = PushButton(
        #     self.tr('Добавить задание'), self, FluentIcon.ADD)
        
        self.ComboBoxType = ComboBox(self)
        self.ComboBoxType.addItems(["В работе", "Выполнено", "Отменено"])
        # self.deleteButton = PushButton(self.tr('Удалить запись'), self, FluentIcon.DELETE)
        # self.updateButton = PushButton(self.tr("Обновить запись"), self, FluentIcon.UPDATE)
        # self.separator = SeparatorWidget(self)
        # self.another_sep = SeparatorWidget(self)

        self.vBoxLayout = QVBoxLayout(self)
        self.buttonLayout = QHBoxLayout()

        self.__initWidget()

    def __initWidget(self):
        self.setFixedHeight(138)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 22, 36, 12)
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(4)
        self.vBoxLayout.addWidget(self.subtitleLabel)
        self.vBoxLayout.addSpacing(4)
        self.vBoxLayout.addLayout(self.buttonLayout, 1)
        self.vBoxLayout.setAlignment(Qt.AlignTop)

        self.buttonLayout.setSpacing(4)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        # self.buttonLayout.addWidget(self.addButton, 0, Qt.AlignLeft)
        self.buttonLayout.addWidget(self.ComboBoxType, 0, Qt.AlignmentFlag.AlignLeft)
        # self.buttonLayout.addWidget(self.another_sep, 0, Qt.AlignRight)
        # self.buttonLayout.addWidget(self.deleteButton, 0, Qt.AlignRight)
        # self.buttonLayout.addWidget(self.separator, 0, Qt.AlignRight)
        # self.buttonLayout.addWidget(self.updateButton, 0, Qt.AlignRight)
        self.buttonLayout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        # self.addButton.installEventFilter(ToolTipFilter(self.addButton))
        self.ComboBoxType.installEventFilter(ToolTipFilter(self.ComboBoxType))
        # self.deleteButton.installEventFilter(ToolTipFilter(self.deleteButton))
        # self.updateButton.installEventFilter(
            # ToolTipFilter(self.updateButton))
        # self.addButton.setToolTip(self.tr('Добавляет запись в таблицу'))
        self.ComboBoxType.setToolTip(self.tr('Добавляет фильтр записей по статусу'))
        # self.deleteButton.setToolTip(self.tr('Удаляет запись из таблицы'))
        # self.updateButton.setToolTip(self.tr('Обновляет запись в таблице'))

        # self.addButton.clicked.connect(lambda: toggleTheme(True))
        # self.updateButton.clicked.connect(signalBus.supportSignal)

        self.subtitleLabel.setTextColor(QColor(96, 96, 96), QColor(216, 216, 216))
        

class AppCard(CardWidget):

    def __init__(self, id, client, owner, title, text, status, start, parent=None):
        super().__init__(parent)
        self.parent_ = parent
        self.id, self.client, self.owner, self.title, self.text, self.status, self.start = id, client, owner, title, text, status, start
        icons = {"В работе": FluentIcon.SYNC, "Отменено": FluentIcon.CANCEL_MEDIUM, "Выполнено": FluentIcon.ACCEPT_MEDIUM}
        self.iconWidget = IconWidget(icons[self.status])
        self.iconWidget.setToolTip(self.tr(f"Задание {self.status.lower()}"))
        self.moreButton = TransparentToolButton(FluentIcon.CANCEL_MEDIUM, self)
        self.moreButton.setToolTip(self.tr("Снять задание!"))
        self.moreButton.clicked.connect(self.cancelApp)
        if self.status != "В работе":
            self.moreButton.hide()
        
        self.titleLabel = StrongBodyLabel(self.title, self)
        self.contentLabel = CaptionLabel(" ".join(self.text.split(" ")[:5]) + "...", self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.setFixedHeight(73)
        self.iconWidget.setFixedSize(28, 28)
        self.contentLabel.setTextColor("#606060", "#d2d2d2")

        self.hBoxLayout.setContentsMargins(20, 11, 20, 11)
        self.hBoxLayout.setSpacing(15)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignVCenter)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignVCenter)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.hBoxLayout.addWidget(self.moreButton, 0, Qt.AlignmentFlag.AlignLeft)

        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.iconWidget, 0, Qt.AlignRight)

        self.clicked.connect(self.editApp)
        
        self.iconWidget.installEventFilter(ToolTipFilter(self.iconWidget))
        self.moreButton.installEventFilter(ToolTipFilter(self.moreButton))
        
        
    def cancelApp(self):
        print("Cancel App")
        rq.cancel_app(self.id)
        self.parent_.parent_.reload()
    
    def editApp(self):
        print("Stronger")
        
        w = mess.UpdateMessageBoxApp(self, self.parent_.parent_)
        if w.exec():
            print(w.TitleEdit.text(), w.TextEdit.toPlainText())
            rq.update_app(self.id, w.TitleEdit.text(), w.TextEdit.toPlainText())
            
        self.parent_.parent_.reload()

class AppCardOwner(CardWidget):

    def __init__(self, id, client, owner, title, text, status, start, parent=None):
        super().__init__(parent)
        self.parent_ = parent
        self.id, self.client, self.owner, self.title, self.text, self.status, self.start = id, client, owner, title, text, status, start
        icons = {"В работе": FluentIcon.SYNC, "Отменено": FluentIcon.CANCEL_MEDIUM, "Выполнено": FluentIcon.ACCEPT_MEDIUM}
        self.iconWidget = IconWidget(icons[self.status])
        self.iconWidget.setToolTip(self.tr(f"Задание {self.status.lower()}"))
        
        self.titleLabel = StrongBodyLabel(self.title, self)
        self.contentLabel = CaptionLabel(" ".join(self.text.split(" ")[:5]) + "...", self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.setFixedHeight(73)
        self.iconWidget.setFixedSize(28, 28)
        self.contentLabel.setTextColor("#606060", "#d2d2d2")

        self.hBoxLayout.setContentsMargins(20, 11, 20, 11)
        self.hBoxLayout.setSpacing(15)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignVCenter)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignVCenter)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.iconWidget, 0, Qt.AlignRight)

        self.clicked.connect(self.editApp)
        
        self.iconWidget.installEventFilter(ToolTipFilter(self.iconWidget))
    
    def editApp(self):
        print("Stronger Owner")
        
        w = mess.CheckMessageBoxApp(self, self.parent_.parent_)
        if w.exec():
            print(w.TitleEdit.text(), w.TextEdit.toPlainText())
            if self.status == "В работе":
                rq.complete_app(self.id)
            
        self.parent_.parent_.reload()
        

class Table(ScrollArea):
    def __init__(self, user, status, parent=None):
        super(Table, self).__init__(parent)
        self.parent_ = parent
        self.user = user
        self.view = QWidget(self)
        self.view.setObjectName('view')
        self.setObjectName('TableWidget')
        StyleSheet.TABLE.apply(self)
        self.vBoxLayout = QVBoxLayout(self.view)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 0, 0, 0)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setMinimumHeight(300)
        self.setMaximumHeight(1314324242)
        self.vBoxLayout.addStretch(1)
        
        self.vBoxLayout.setSpacing(6)
        self.vBoxLayout.setContentsMargins(20, 0, 30, 10)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.data = []
        
        self.user.user = rq.get_apps(self.user.user)
        table = self.user.user.apps
        
        self.data = [i.get_data() for i in table]
        
        for i in self.data:
            if i["status"] == status:
                self.addCard(i["id"], i["client"], i["owner"], i["title"], i["text"], i["status"], i["start"])
        
        
    def addCard(self, id, client, owner, title, text, status, start):
        if self.parent_.__class__ == OwnerWidget:
            card = AppCardOwner(id, client, owner, title, text, status, start, self)
        else:
            card = AppCard(id, client, owner, title, text, status, start, self)
        self.vBoxLayout.addWidget(card, alignment=Qt.AlignTop)


class ClientWidget(QtWidgets.QWidget):
    
    def __init__(self, user, parent=None):
        super(ClientWidget, self).__init__(parent)
        self.user = user
        self.setObjectName('ClientWidget')
        
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setAlignment(Qt.AlignTop)
        self.verticalLayout.setContentsMargins(36, 0, 36, 5)
        self.verticalLayout.setObjectName("horizontalLayout")
        
        self.label = ToolBar(self.tr("Задания"), "Надо что то написать!", self)
        self.type = self.label.ComboBoxType.text()
        self.label.ComboBoxType.currentTextChanged.connect(self.change_type)
        
        self.label.addButton.clicked.connect(
            self.add)
        self.label.setObjectName("MainLabel")
        
        self.verticalLayout.addWidget(self.label, 0, Qt.AlignTop)
        self.table = Table(self.user, self.type, self)
        self.verticalLayout.addWidget(self.table, 1)
        self.table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        
        
        with open(r'.\app\resource\qss\dark\tables.qss', encoding='utf-8') as f:
            self.setStyleSheet(f.read())
        # StyleSheet.PASSENGERS.apply(self)
        
    def add(self):
        w = mess.AddMessageBoxTask(self.user, self)
        if w.exec():
            print(w.TitleEdit.text(), w.TextEdit.toPlainText())
            rq.insert_app(self.user.id, w.TitleEdit.text(), w.TextEdit.toPlainText())
        
        self.reload()

    def change_type(self):
        self.type = self.label.ComboBoxType.text()
        self.reload()
        
    def reload(self):
        self.verticalLayout.removeWidget(self.table)
        self.table.hide()
        self.table = Table(self.user, self.type, self)
        self.verticalLayout.addWidget(self.table, 1)

    # def remove(self):
    #     indexs = set([i.row() for i in self.table.selectedIndexes()])
        
    #     for i in indexs:
    #         print(self.table.item(i, 0).text())
    #         rq.delete_user(self.table.item(i, 0).text())
        
    #     self.table.reload()
    
    # def update(self):
    #     index = self.table.currentRow()
    #     res = []
    #     for i, col in enumerate(self.columns):
    #         print(i, index)
    #         res.append(self.table.item(index, i).text())
        
    #     w = mess.UpdateMessageBoxPassengers(res, self)
    #     if w.exec():
    #         print(w.id, w.NameEdit.text(), w.LastEdit.text(), w.MiddleEdit.text(), w.mail.text(), w.date.date.toString(Qt.DateFormat.ISODate), w.address.text(), 
    #               w.number.text(), w.gender.text(), w.pass_series.text(), w.pass_number.text())
    #         rq.update_user(w.id, w.NameEdit.text(), w.LastEdit.text(), w.MiddleEdit.text(), w.mail.text(), w.date.date.toString(Qt.DateFormat.ISODate), w.address.text(), 
    #                        w.number.text(), w.gender.text(), w.pass_series.text(), w.pass_number.text())
    #         self.table.reload()
    
class OwnerWidget(QtWidgets.QWidget):
    
    def __init__(self, user, parent=None):
        super(OwnerWidget, self).__init__(parent)
        self.user = user
        self.setObjectName('ClientWidget')
        
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setAlignment(Qt.AlignTop)
        self.verticalLayout.setContentsMargins(36, 0, 36, 5)
        self.verticalLayout.setObjectName("horizontalLayout")
        
        self.label = ToolBarOwner(self.tr("Задания"), "Надо что то написать!", self)
        self.type = self.label.ComboBoxType.text()
        self.label.ComboBoxType.currentTextChanged.connect(self.change_type)
        
        self.label.setObjectName("MainLabel")
        
        self.verticalLayout.addWidget(self.label, 0, Qt.AlignTop)
        self.table = Table(self.user, self.type, self)
        self.verticalLayout.addWidget(self.table, 1)
        self.table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        
        
        with open(r'.\app\resource\qss\dark\tables.qss', encoding='utf-8') as f:
            self.setStyleSheet(f.read())
        # StyleSheet.PASSENGERS.apply(self)

    def change_type(self):
        self.type = self.label.ComboBoxType.text()
        self.reload()
        
    def reload(self):
        self.verticalLayout.removeWidget(self.table)
        self.table.hide()
        self.table = Table(self.user, self.type, self)
        self.verticalLayout.addWidget(self.table, 1)