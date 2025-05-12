# coding:utf-8
import os
import sys
from inspect import getsourcefile
from pathlib import Path

os.chdir(Path(getsourcefile(lambda: 0)).resolve().parent)


from PyQt6.QtCore import QLocale, Qt, QTranslator
from PyQt6.QtWidgets import QApplication

from common.application import SingletonApplication
from common.config import config, Language
from common.setting import APP_NAME
from common.dpi_manager import DPI_SCALE
from view.main_window import MainWindow
from view.login import LoginWindow

# fix bug: qt.qpa.plugin: Could not load the Qt platform plugin "xcb"
if "QT_QPA_PLATFORM_PLUGIN_PATH" in os.environ:
    os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH")

# enable high dpi scale
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_SCALE_FACTOR"] = str(DPI_SCALE)

QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

app = SingletonApplication(sys.argv, APP_NAME)
app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
app.setApplicationName(APP_NAME)

# Internationalization
# translator = QTranslator()
# language = config.get(config.language)  # type: Language

# app.installTranslator(translator)

# create main window
project = LoginWindow()
project.show()

app.exec_()