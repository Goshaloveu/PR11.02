# coding:utf-8
import os
import sys
from inspect import getsourcefile
from pathlib import Path

# Get the parent directory (repository root)
current_dir = Path(getsourcefile(lambda: 0)).resolve().parent
parent_dir = current_dir.parent
os.chdir(parent_dir)

# Add the parent directory to Python path so we can use absolute imports
sys.path.append(str(parent_dir))

from PyQt6.QtCore import QLocale, Qt, QTranslator
from PyQt6.QtWidgets import QApplication

from app.common.application import SingletonApplication
from app.common.config import config, Language
from app.common.setting import APP_NAME
from app.common.dpi_manager import DPI_SCALE
from app.view.MainLogin import MainLoginWindow
from app.common.db.database import init_db

# enable high dpi scale
# os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
# os.environ["QT_SCALE_FACTOR"] = str(DPI_SCALE)

if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = SingletonApplication(sys.argv, APP_NAME)
    app.setApplicationName(APP_NAME)


    # Initialize database
    init_db()

    # create main window
    project = MainLoginWindow()
    project.show()

    app.exec()