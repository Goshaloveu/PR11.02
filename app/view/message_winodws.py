from qfluentwidgets import MessageBoxBase, SubtitleLabel, LineEdit, PushButton, CaptionLabel
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QListWidgetItem, QFrame, QTreeWidgetItem, QHBoxLayout,
                             QTreeWidgetItemIterator, QTableWidgetItem)
from qfluentwidgets import TreeWidget, TableWidget, ListWidget, HorizontalFlipView, TitleLabel
from .gallery_interface import GalleryInterface
from ..common.translator import Translator
from ..common.style_sheet import StyleSheet
from PySide6 import QtWidgets

from PySide6.QtCore import Qt, QUrl, QEvent, QDate, QTime
from PySide6.QtGui import QDesktopServices, QPainter, QPen, QColor
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame

from qfluentwidgets import (ScrollArea, PushButton, ToolButton, FluentIcon,
                            isDarkTheme, IconWidget, Theme, ToolTipFilter, TitleLabel, CaptionLabel,
                            StrongBodyLabel, BodyLabel, TimePicker, CalendarPicker, ComboBox, TextEdit, toggleTheme)
from ..common.config import cfg, FEEDBACK_URL, HELP_URL, EXAMPLE_URL
from ..common.icon import Icon
from ..common.style_sheet import StyleSheet
from ..common.signal_bus import signalBus
import db.requests as rq
import re
from datetime import date
import pymorphy2

morph = pymorphy2.MorphAnalyzer()


class AddMessageBoxPassengers(MessageBoxBase):
    """ Custom message box """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel('Добавление данных', self)
        
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        
        self.firstH = QHBoxLayout(self)
        self.firstH.setObjectName("1_HorizontalLayout")
        self.NameEdit = LineEdit(self)
        self.NameEdit.setPlaceholderText('Имя')
        self.NameEdit.setClearButtonEnabled(True)
        self.firstH.addWidget(self.NameEdit)
        
        self.LastEdit = LineEdit(self)
        self.LastEdit.setPlaceholderText('Фамилия')
        self.LastEdit.setClearButtonEnabled(True)
        self.firstH.addWidget(self.LastEdit)
        
        self.MiddleEdit = LineEdit(self)
        self.MiddleEdit.setPlaceholderText('Отчество')
        self.MiddleEdit.setClearButtonEnabled(True)
        self.firstH.addWidget(self.MiddleEdit)
        
        self.secondH = QHBoxLayout(self)
        self.secondH.setObjectName("2_HorizontalLayout")
        self.pass_series = LineEdit(self)
        self.pass_series.setPlaceholderText('Серия паспорта')
        self.pass_series.setClearButtonEnabled(True)
        self.secondH.addWidget(self.pass_series)
        
        self.pass_number = LineEdit(self)
        self.pass_number.setPlaceholderText('Номер паспорта')
        self.pass_number.setClearButtonEnabled(True)
        self.secondH.addWidget(self.pass_number)
        
        self.gender = ComboBox(self)
        self.gender.addItems(["m", "f"])
        self.secondH.addWidget(self.gender)
        
        self.thirdH = QHBoxLayout(self)
        self.thirdH.setObjectName("3_HorizontalLayout")
        self.mail = LineEdit(self)
        self.mail.setPlaceholderText('Почта')
        self.mail.setClearButtonEnabled(True)
        self.thirdH.addWidget(self.mail)
        
        self.number = LineEdit(self)
        self.number.setPlaceholderText('Номер телефона')
        self.number.setClearButtonEnabled(True)
        self.thirdH.addWidget(self.number)
        
        self.fourthH = QHBoxLayout(self)
        self.fourthH.setObjectName("4_HorizontalLayout")
        self.date = CalendarPicker(self)
        self.date.setText("Дата рождения")
        self.fourthH.addWidget(self.date)
        
        self.address = LineEdit(self)
        self.address.setPlaceholderText("Адрес места жительства")
        self.address.setClearButtonEnabled(True)
        self.fourthH.addWidget(self.address)
        

        self.warningLabelpass = CaptionLabel("Неправильные данные паспорта")
        self.warningLabelpass.setTextColor("#cf1010", QColor(255, 28, 32))
        self.warningLabelmail = CaptionLabel("Некорректный почтовый адрес")
        self.warningLabelmail.setTextColor("#cf1010", QColor(255, 28, 32))
        self.warningLabelfio = CaptionLabel("ФИО может состоять только из латиницы и кирилицы и знака -")
        self.warningLabelfio.setTextColor("#cf1010", QColor(255, 28, 32))
        self.warningLabelnumber = CaptionLabel("Некорректный номер телефона, номер должен начинаться на 8 или +7 и состоять из 11 цифр")
        self.warningLabelnumber.setTextColor("#cf1010", QColor(255, 28, 32))
        self.warningLabelNull = CaptionLabel("Поля формы не могут быть пустыми!")
        self.warningLabelNull.setTextColor("#cf1010", QColor(255, 28, 32))

        # add widget to view layout
        self.verticalLayout.addWidget(self.titleLabel)
        self.verticalLayout.addLayout(self.firstH)
        self.verticalLayout.addLayout(self.secondH)
        self.verticalLayout.addLayout(self.thirdH)
        self.verticalLayout.addLayout(self.fourthH)
        
        
        self.viewLayout.addLayout(self.verticalLayout)
        self.viewLayout.addWidget(self.warningLabelNull)
        self.warningLabelNull.hide()
        self.viewLayout.addWidget(self.warningLabelpass)
        self.warningLabelpass.hide()
        self.viewLayout.addWidget(self.warningLabelmail)
        self.warningLabelmail.hide()
        self.viewLayout.addWidget(self.warningLabelnumber)
        self.warningLabelnumber.hide()
        self.viewLayout.addWidget(self.warningLabelfio)
        self.warningLabelfio.hide()

        # change the text of button
        self.yesButton.setText('Обновить данные')

        self.widget.setMinimumWidth(350)

        # self.hideYesButton()

    def validate(self):
        """ Rewrite the virtual method """
        isPassSeriesValid = re.fullmatch(r"\d{4}", self.pass_series.text())
        isPassNumberValid = re.fullmatch(r"\d{6}", self.pass_number.text())
        isValidMail =  bool(re.fullmatch(r"\w+@\w+\.\w+", self.mail.text(), re.IGNORECASE))
        comp = re.compile("^[a-zA-Zа-яА-ЯёЁ-]*$")
        isValidName = bool(comp.fullmatch(self.NameEdit.text()))
        isValidLast = bool(comp.fullmatch(self.LastEdit.text()))
        isValidMiddle = bool(comp.fullmatch(self.MiddleEdit.text()))
        isValidNumber = bool(re.fullmatch(r"^(?:\+7|8)\d{10}$", self.number.text()))
        
        
        
        
        nullable = not bool([i for i in filter(lambda x: len(x) == 0, [self.pass_series.text(), self.pass_number.text(), self.mail.text(), self.NameEdit.text(),
                                                                            self.LastEdit.text(), self.MiddleEdit.text(), self.number.text(), self.address.text(),
                                                                            self.date.date.toString(Qt.DateFormat.ISODate)])])
        self.warningLabelNull.setHidden(nullable)
        self.warningLabelpass.setHidden(bool(isPassNumberValid and isPassSeriesValid))
        self.warningLabelmail.setHidden(bool(isValidMail))
        self.warningLabelfio.setHidden(bool(isValidName and isValidLast and isValidMiddle))
        self.warningLabelnumber.setHidden(bool(isValidNumber))
        
        isValid = isPassNumberValid and isPassSeriesValid and isValidMail and isValidName and isValidLast and isValidMiddle and isValidNumber and nullable
        
        return isValid


class AddMessageBoxTask(MessageBoxBase):
    """ Custom message box """

    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.titleLabel = SubtitleLabel('Добавление задания', self)
        
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")

        name, last = morph.parse(self.user.first)[0].inflect({'gent'}).word, morph.parse(self.user.last)[0].inflect({'gent'}).word
        self.label = BodyLabel(f"Задание от {str.capitalize(name)} {str.capitalize(last)}", self)
        self.firstH = QHBoxLayout(self)
        self.firstH.setObjectName("1_HorizontalLayout")
        self.TitleEdit = LineEdit(self)
        self.TitleEdit.setMaxLength(30)
        self.TitleEdit.setPlaceholderText('Заголовок')
        self.TitleEdit.setClearButtonEnabled(True)
        self.firstH.addWidget(self.TitleEdit)
        
        self.secondH = QHBoxLayout(self)
        self.secondH.setObjectName("2_HorizontalLayout")
        self.TextEdit = TextEdit(self)
        self.TextEdit.setPlaceholderText('Описание задачи . . .')
        self.TextEdit.setMarkdown(
            "## Сделайте для меня пожалуйста следующее: \n * Найдите мне единорога 🦄 \n * Подарите мне лошадь 🐴 ")
        self.TextEdit.setMinimumSize(500, 150)
        self.secondH.addWidget(self.TextEdit)

        self.warningLabelNull = CaptionLabel("Заголовок формы не может быть пустым!")
        self.warningLabelNull.setTextColor("#cf1010", QColor(255, 28, 32))

        # add widget to view layout
        self.verticalLayout.addWidget(self.titleLabel)
        self.verticalLayout.addWidget(self.label)
        self.verticalLayout.addLayout(self.firstH)
        self.verticalLayout.addLayout(self.secondH)
        
        
        self.viewLayout.addLayout(self.verticalLayout)
        self.viewLayout.addWidget(self.warningLabelNull)
        self.warningLabelNull.hide()
        
        # change the text of button
        self.yesButton.setText('Добавить')
        self.cancelButton.setText('Отмена')

        self.widget.setMinimumWidth(350)

        # self.hideYesButton()

    def validate(self):
        """ Rewrite the virtual method """
        nullable = bool(self.TitleEdit.text())
        self.warningLabelNull.setHidden(nullable)
        isValid = nullable
        
        return isValid


class UpdateMessageBoxApp(MessageBoxBase):
    def __init__(self, user, parent=None):
        super(UpdateMessageBoxApp, self).__init__(parent)
        self.user = user
        self.titleLabel = SubtitleLabel('Задание', self)
        
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")

        self.firstH = QHBoxLayout(self)
        self.firstH.setObjectName("1_HorizontalLayout")
        self.TitleEdit = LineEdit(self)
        self.TitleEdit.setMaxLength(30)
        self.TitleEdit.setPlaceholderText('Заголовок')
        self.TitleEdit.setText(self.user.title)
        self.TitleEdit.setClearButtonEnabled(True)
        self.firstH.addWidget(self.TitleEdit)
        
        self.secondH = QHBoxLayout(self)
        self.secondH.setObjectName("2_HorizontalLayout")
        self.TextEdit = TextEdit(self)
        self.TextEdit.setPlaceholderText('Описание задачи . . .')
        self.TextEdit.setText(self.user.text)
        self.TextEdit.setMinimumSize(500, 150)
        self.secondH.addWidget(self.TextEdit)

        self.warningLabelNull = CaptionLabel("Заголовок формы не может быть пустым!")
        self.warningLabelNull.setTextColor("#cf1010", QColor(255, 28, 32))

        # add widget to view layout
        self.verticalLayout.addWidget(self.titleLabel)
        self.verticalLayout.addLayout(self.firstH)
        self.verticalLayout.addLayout(self.secondH)
        
        
        self.viewLayout.addLayout(self.verticalLayout)
        self.viewLayout.addWidget(self.warningLabelNull)
        self.warningLabelNull.hide()
        
        # change the text of button
        if self.user.status == "В работе":
            self.yesButton.setText('Обновить')
            self.cancelButton.setText('Отмена')
        else:
            self.TitleEdit.setEnabled(False)
            self.TextEdit.setEnabled(False)
            self.cancelButton.setText('Ок')
            self.yesButton.hide()

        self.widget.setMinimumWidth(350)

        # self.hideYesButton()

    def validate(self):
        """ Rewrite the virtual method """
        nullable = bool(self.TitleEdit.text())
        self.warningLabelNull.setHidden(nullable)
        isValid = nullable
        
        return isValid
        
class CheckMessageBoxApp(MessageBoxBase):
    def __init__(self, user, parent=None):
        super(CheckMessageBoxApp, self).__init__(parent)
        self.user = user
        self.titleLabel = SubtitleLabel('Подробнее о задании', self)
        
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")

        self.firstH = QHBoxLayout(self)
        self.firstH.setObjectName("1_HorizontalLayout")
        self.TitleEdit = LineEdit(self)
        self.TitleEdit.setMaxLength(30)
        self.TitleEdit.setText(self.user.title)
        self.TitleEdit.setEnabled(False)
        self.firstH.addWidget(self.TitleEdit)
        
        self.secondH = QHBoxLayout(self)
        self.secondH.setObjectName("2_HorizontalLayout")
        self.TextEdit = TextEdit(self)
        self.TextEdit.setText(self.user.text)
        self.TextEdit.setEnabled(False)
        self.TextEdit.setMinimumSize(500, 150)
        self.secondH.addWidget(self.TextEdit)

        # add widget to view layout
        self.verticalLayout.addWidget(self.titleLabel)
        self.verticalLayout.addLayout(self.firstH)
        self.verticalLayout.addLayout(self.secondH)
        
        
        self.viewLayout.addLayout(self.verticalLayout)
        
        # change the text of button
        if self.user.status == "В работе":
            self.yesButton.setText('Выполнить')
            self.cancelButton.setText('Отмена')
        else:
            self.yesButton.setText('Ок')
            self.cancelButton.hide()

        self.widget.setMinimumWidth(350)
    
    
# class UpdateMessageBoxPassengers(AddMessageBoxPassengers):
#     """ Custom message box """

#     def __init__(self, row_data, parent=None):
#         super(UpdateMessageBoxPassengers, self).__init__(parent)
        
#         self.id = row_data[0]
#         self.NameEdit.setText(row_data[1])
#         self.LastEdit.setText(row_data[2])
#         self.MiddleEdit.setText(row_data[3])
#         self.pass_series.setText(str(row_data[4]))
#         self.pass_number.setText(str(row_data[5]))
#         self.mail.setText(row_data[6])
#         self.date.setDate(QDate.fromString(row_data[7], "yyyy-MM-dd"))
#         self.address.setText(row_data[8])
#         self.number.setText(str(row_data[9]))
#         self.gender.setCurrentIndex(0 if row_data[10] == "m" else 1)
        
#         self.yesButton.setText('Обновить')
#         self.titleLabel.setText("Обновление данных")


class AddMessageBoxFlight(MessageBoxBase):
    """ Custom message box """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel('Добавление данных', self)
        
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        
        self.firstH = QHBoxLayout(self)
        self.firstH.setObjectName("1_HorizontalLayout")
        
        self.category = ComboBox(self)
        self.category.addItems(["A", "B", "C"])
        self.firstH.addWidget(self.category)
        
        self.numberEdit = LineEdit(self)
        self.numberEdit.setPlaceholderText('Номер')
        self.numberEdit.setClearButtonEnabled(True)
        self.numberEdit.setMaxLength(3)
        self.firstH.addWidget(self.numberEdit)
        
        self.status = ComboBox(self)
        self.status.addItems(["fly", "end", "start"])
        self.firstH.addWidget(self.status)
        
        self.secondH = QHBoxLayout(self)
        self.secondH.setObjectName("2_HorizontalLayout")
        
        self.FromEdit = LineEdit(self)
        self.FromEdit.setPlaceholderText('Откуда')
        self.FromEdit.setClearButtonEnabled(True)
        self.secondH.addWidget(self.FromEdit)
        
        self.DirectEdit = LineEdit(self)
        self.DirectEdit.setPlaceholderText('Куда')
        self.DirectEdit.setClearButtonEnabled(True)
        self.secondH.addWidget(self.DirectEdit)
        
        self.thirdH = QHBoxLayout(self)
        self.thirdH.setObjectName("3_HorizontalLayout")
        
        self.date = CalendarPicker(self)
        self.date.setText("Дата вылета")
        self.thirdH.addWidget(self.date)
        
        self.fourthH = QVBoxLayout(self)
        self.fourthH.setObjectName("4_VerticalLayout")
        
        self.timeLabel = BodyLabel('Время вылета', self)
        self.fourthH.addWidget(self.timeLabel)
        
        self.time = TimePicker(self)
        self.fourthH.addWidget(self.time)
        self.thirdH.addLayout(self.fourthH)
        

        self.warningLabelDirect = CaptionLabel("Пункт назначения не может быть равен пункту отправления")
        self.warningLabelDirect.setTextColor("#cf1010", QColor(255, 28, 32))

        # add widget to view layout
        self.verticalLayout.addWidget(self.titleLabel)
        self.verticalLayout.addLayout(self.firstH)
        self.verticalLayout.addLayout(self.secondH)
        self.verticalLayout.addLayout(self.thirdH)
        
        
        self.viewLayout.addLayout(self.verticalLayout)
        self.viewLayout.addWidget(self.warningLabelDirect)
        self.warningLabelDirect.hide()

        # change the text of button
        self.yesButton.setText('Добавить')
        self.cancelButton.setText('Отмена')

        self.widget.setMinimumWidth(350)

        # self.hideYesButton()

    def validate(self):
        """ Rewrite the virtual method """
        
        isDirectValid = self.DirectEdit.text() != self.FromEdit.text()
        self.warningLabelDirect.setHidden(isDirectValid)
        
        return isDirectValid


class UpdateMessageBoxFlight(AddMessageBoxFlight):
    """ Custom message box """

    def __init__(self, row_data, parent=None):
        super(UpdateMessageBoxFlight, self).__init__(parent)
        
        cat = row_data[1][0]
        ser = row_data[1][1:]
        
        self.category.setCurrentIndex(["A", "B", "C"].index(cat))
        self.numberEdit.setText(ser)
        self.status.setCurrentIndex(["fly", "end", "start"].index(row_data[-1]))
        self.FromEdit.setText(row_data[2])
        self.DirectEdit.setText(row_data[3])
        self.date.setDate(QDate.fromString(row_data[4], "yyyy-MM-dd"))
        self.time.setTime(QTime.fromString(row_data[5], "hh:mm:ss"))
        
        self.yesButton.setText('Обновить')
        self.titleLabel.setText("Обновление данных")
        
        
class AddMessageBoxTicket(MessageBoxBase):
    """ Custom message box """

    def __init__(self, data, parent=None):
        super(AddMessageBoxTicket, self).__init__(parent)
        self.titleLabel = SubtitleLabel('Добавление данных', self)
        
        self.reis = {i["flight"].number: i["flight"].id for i in data}
        self.reis_set = set(self.reis.keys())
        self.passengers = set([str(i.id) for i in rq.get_table("passengers")])
        print(self.passengers)
        
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        
        self.firstH = QHBoxLayout(self)
        self.firstH.setObjectName("1_HorizontalLayout")
        
        self.category = ComboBox(self)
        self.category.addItems(["A", "B", "C"])
        self.firstH.addWidget(self.category)
        
        self.numberEdit = LineEdit(self)
        self.numberEdit.setPlaceholderText('Номер рейса')
        self.numberEdit.setClearButtonEnabled(True)
        self.numberEdit.setMaxLength(3)
        self.firstH.addWidget(self.numberEdit)
        
        self.status = ComboBox(self)
        self.status.addItems(["available", "sold", "expired"])
        self.firstH.addWidget(self.status)
        
        self.secondH = QHBoxLayout(self)
        self.secondH.setObjectName("2_HorizontalLayout")
        
        self.FromEdit = LineEdit(self)
        self.FromEdit.setPlaceholderText('Номер пассажира')
        self.FromEdit.setClearButtonEnabled(True)
        self.secondH.addWidget(self.FromEdit)
        
        self.PlaceEdit = LineEdit(self)
        self.PlaceEdit.setPlaceholderText('Номер места в самолете')
        self.PlaceEdit.setClearButtonEnabled(True)
        self.secondH.addWidget(self.PlaceEdit)
        
        self.thirdH = QHBoxLayout(self)
        self.thirdH.setObjectName("3_HorizontalLayout")
        
        self.date = CalendarPicker(self)
        self.date.setText("Дата покупки")
        self.thirdH.addWidget(self.date)
        
        self.fourthH = QVBoxLayout(self)
        self.fourthH.setObjectName("4_VerticalLayout")
        
        self.timeLabel = BodyLabel('Время покупки', self)
        self.fourthH.addWidget(self.timeLabel)
        
        self.time = TimePicker(self)
        self.fourthH.addWidget(self.time)
        self.thirdH.addLayout(self.fourthH)
        

        self.warningLabelPassenger = CaptionLabel("Пассажира с таким номером не существует")
        self.warningLabelFlight = CaptionLabel("Рейса с таким номером не существует")
        self.warningLabelPassenger.setTextColor("#cf1010", QColor(255, 28, 32))
        self.warningLabelFlight.setTextColor("#cf1010", QColor(255, 28, 32))
        self.warningLabelNull = CaptionLabel("Поля рейса, места и статуса не могут быть пустыми!")
        self.warningLabelNull.setTextColor("#cf1010", QColor(255, 28, 32))
        self.warningLabelOp = CaptionLabel("Такой билет уже существует!")
        self.warningLabelOp.setTextColor("#cf1010", QColor(255, 28, 32))

        # add widget to view layout
        self.verticalLayout.addWidget(self.titleLabel)
        self.verticalLayout.addLayout(self.firstH)
        self.verticalLayout.addLayout(self.secondH)
        self.verticalLayout.addLayout(self.thirdH)
        
        
        self.viewLayout.addLayout(self.verticalLayout)
        self.viewLayout.addWidget(self.warningLabelPassenger)
        self.warningLabelPassenger.hide()
        self.viewLayout.addWidget(self.warningLabelFlight)
        self.warningLabelFlight.hide()
        self.viewLayout.addWidget(self.warningLabelNull)
        self.warningLabelNull.hide()
        self.viewLayout.addWidget(self.warningLabelOp)
        self.warningLabelOp.hide()

        # change the text of button
        self.yesButton.setText('Добавить')
        self.cancelButton.setText('Отмена')

        self.widget.setMinimumWidth(350)

        # self.hideYesButton()

    def validate(self):
        """ Rewrite the virtual method """
        
        isPassengerValid = True
        
        if self.FromEdit.text():
            isPassengerValid = self.FromEdit.text() in self.passengers
            self.warningLabelPassenger.setHidden(isPassengerValid)

        isFlightValid = (self.category.text() + self.numberEdit.text()) in self.reis_set
        self.warningLabelFlight.setHidden(isFlightValid)
        
        nullable = not bool([i for i in filter(lambda x: len(x) == 0, [self.numberEdit.text(), self.PlaceEdit.text()])])

        self.warningLabelNull.setHidden(nullable)
        
        isExist = not rq.check_ticket(self.reis[self.category.text() + self.numberEdit.text()], self.PlaceEdit.text())
        # ex = rq.a_check_ticket(self.reis[self.category.text() + self.numberEdit.text()], self.PlaceEdit.text())
        # print(ex.__dict__)
        # print(self.category.text() + self.numberEdit.text(), self.reis[self.category.text() + self.numberEdit.text()])
        self.warningLabelOp.setHidden(isExist)
        
        isValid = isPassengerValid and isFlightValid and nullable and isExist
        
        return isValid


class UpdateMessageBoxTicket(AddMessageBoxTicket):
    """ Custom message box """

    def __init__(self, data, row_data, parent=None):
        super(UpdateMessageBoxTicket, self).__init__(data, parent)
        
        row_data = [i if i != "None" else None for i in row_data]
        cat = row_data[1][0]
        ser = row_data[1][1:]
        
        self.category.setCurrentIndex(["A", "B", "C"].index(cat))
        self.numberEdit.setText(ser)
        self.status.setCurrentIndex(["available", "sold", "expired"].index(row_data[-1]))
        self.FromEdit.setText(row_data[3])
        self.PlaceEdit.setText(row_data[2])
        if row_data[4]:
            self.date.setDate(QDate.fromString(row_data[4].split(" ")[0], "yyyy-MM-dd"))
            self.time.setTime(QTime.fromString(row_data[4].split(" ")[1], "hh:mm:ss"))
        
        self.numberEdit.setReadOnly(True)
        self.numberEdit.setClearButtonEnabled(False)
        self.PlaceEdit.setReadOnly(True)
        self.PlaceEdit.setClearButtonEnabled(False)
        self.category.setEnabled(False)
        
        self.yesButton.setText('Обновить')
        self.titleLabel.setText("Обновление данных")
    
    def validate(self):
        """ Rewrite the virtual method """
        
        isPassengerValid = True
        
        if self.FromEdit.text():
            isPassengerValid = self.FromEdit.text() in self.passengers
            self.warningLabelPassenger.setHidden(isPassengerValid)

        isFlightValid = (self.category.text() + self.numberEdit.text()) in self.reis_set
        self.warningLabelFlight.setHidden(isFlightValid)
        
        nullable = not bool([i for i in filter(lambda x: len(x) == 0, [self.numberEdit.text(), self.PlaceEdit.text()])])

        self.warningLabelNull.setHidden(nullable)
        
        # isExist = not rq.check_ticket(self.reis[self.category.text() + self.numberEdit.text()], self.PlaceEdit.text())
        # ex = rq.a_check_ticket(self.reis[self.category.text() + self.numberEdit.text()], self.PlaceEdit.text())
        # print(ex.__dict__)
        # print(self.category.text() + self.numberEdit.text(), self.reis[self.category.text() + self.numberEdit.text()])
        # self.warningLabelOp.setHidden(isExist)
        
        isValid = isPassengerValid and isFlightValid and nullable \
                                    # and isExist
        
        return isValid