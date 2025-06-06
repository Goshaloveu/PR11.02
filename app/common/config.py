# coding:utf-8
import json
import sys
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Union

import darkdetect
from sqlalchemy import URL
from PyQt6.QtCore import Qt, QStandardPaths, QObject, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QGuiApplication

from .exception_handler import exceptionHandler
from .singleton import Singleton
from .setting import APP_NAME, CONFIG_FOLDER, CONFIG_FILE

# config.py
import os

# DB_USER = os.getenv("DB_USER", "root")
# DB_PASSWORD = os.getenv("DB_PASSWORD", "your_mysql_password")
# DB_HOST = os.getenv("DB_HOST", "localhost")
# DB_PORT = os.getenv("DB_PORT", "3306")
# DB_NAME = os.getenv("DB_NAME", "terra")

# Формат: mysql+<driver>://<user>:<password>@<host>[:<port>]/<database>
DATABASE_URL = url = URL.create(
    "mysql+pymysql",
    username="root",
    password="S@nktum56",  # plain (unescaped) text
    host="localhost",
    database="terra",
)

# --- Настройки безопасности ---
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_for_jwt_or_sessions") # Нужен для токенов/сессий
PASSWORD_CONTEXT_SCHEMES = ["bcrypt"] # Схема хеширования паролей

# --- Прочее ---
# Добавь другие настройки по необходимости

class Language(Enum):
    """ Language enumeration """
    RUSSIAN = "ru"
    ENGLISH = "en"
    AUTO = "Auto"

class Theme(Enum):
    """ Theme enumeration """
    LIGHT = "Light"
    DARK = "Dark"
    AUTO = "Auto"

class Config:
    def __init__(self):
        # Basic settings
        self.language = Language.RUSSIAN
        self.theme = Theme.LIGHT
        
        # DPI settings
        self.dpiScale = "Auto"
        
        # Window settings
        self.minimizeToTray = True
        self.enableAcrylicBackground = False
    
    def get(self, item):
        if isinstance(item, str):
            return getattr(self, item, None)
        return item
    
    def set(self, item, value):
        if isinstance(item, str):
            setattr(self, item, value)
        else:
            setattr(self, item.__name__, value)

config = Config()

# class ConfigValidator:
#     """ Config validator """

#     def validate(self, value) -> bool:
#         """ Verify whether the value is legal """
#         return True

#     def correct(self, value):
#         """ correct illegal value """
#         return value


# class RangeValidator(ConfigValidator):
#     """ Range validator """

#     def __init__(self, min, max):
#         self.min = min
#         self.max = max
#         self.range = (min, max)

#     def validate(self, value) -> bool:
#         return self.min <= value <= self.max

#     def correct(self, value):
#         return min(max(self.min, value), self.max)


# class OptionsValidator(ConfigValidator):
#     """ Options validator """

#     def __init__(self, options: Union[Iterable, Enum]) -> None:
#         if not options:
#             raise ValueError("The `options` can't be empty.")

#         if isinstance(options, Enum):
#             options = options._member_map_.values()

#         self.options = list(options)

#     def validate(self, value) -> bool:
#         return value in self.options

#     def correct(self, value):
#         return value if self.validate(value) else self.options[0]


# class BoolValidator(OptionsValidator):
#     """ Boolean validator """

#     def __init__(self):
#         super().__init__([True, False])


# class FolderValidator(ConfigValidator):
#     """ Folder validator """

#     def validate(self, value: Union[str, Path]) -> bool:
#         return Path(value).exists()

#     def correct(self, value: Union[str, Path]):
#         path = Path(value)
#         try:
#             path.mkdir(exist_ok=True, parents=True)
#         except:
#             pass
#         return str(path.absolute()).replace("\\", "/")


# class FolderListValidator(ConfigValidator):
#     """ Folder list validator """

#     def validate(self, value: List[Union[str, Path]]) -> bool:
#         return all(Path(i).exists() for i in value)

#     def correct(self, value: List[Union[str, Path]]):
#         folders = []
#         for folder in value:
#             path = Path(folder)
#             if path.exists():
#                 folders.append(str(path.absolute()).replace("\\", "/"))

#         return folders


# class ColorValidator(ConfigValidator):
#     """ RGB color validator """

#     def __init__(self, default):
#         self.default = QColor(default)

#     def validate(self, color) -> bool:
#         try:
#             return QColor(color).isValid()
#         except:
#             return False

#     def correct(self, value):
#         return QColor(value) if self.validate(value) else self.default


# class ConfigSerializer:
#     """ Config serializer """

#     def serialize(self, value):
#         """ serialize config value """
#         return value

#     def deserialize(self, value):
#         """ deserialize config from config file's value """
#         return value


# class EnumSerializer(ConfigSerializer):
#     """ enumeration class serializer """

#     def __init__(self, enumClass):
#         self.enumClass = enumClass

#     def serialize(self, value: Enum):
#         return value.value

#     def deserialize(self, value):
#         return self.enumClass(value)


# class ColorSerializer(ConfigSerializer):
#     """ QColor serializer """

#     def serialize(self, value: QColor):
#         return value.name()

#     def deserialize(self, value):
#         if isinstance(value, list):
#             return QColor(*value)

#         return QColor(value)


# class ConfigItem:
#     """ Config item """

#     def __init__(self, group: str, name: str, default, validator: ConfigValidator = None,
#                  serializer: ConfigSerializer = None, restart=False):
#         """
#         Parameters
#         ----------
#         group: str
#             config group name

#         name: str
#             config item name, can be empty

#         default:
#             default value

#         options: list
#             options value

#         serializer: ConfigSerializer
#             config serializer

#         restart: bool
#             whether to restart the application after updating the configuration item
#         """
#         self.group = group
#         self.name = name
#         self.validator = validator or ConfigValidator()
#         self.serializer = serializer or ConfigSerializer()
#         self.__value = default
#         self.value = default
#         self.restart = restart

#     @property
#     def value(self):
#         """ get the value of config item """
#         return self.__value

#     @value.setter
#     def value(self, v):
#         self.__value = self.validator.correct(v)

#     @property
#     def key(self):
#         """ get the config key separated by `.` """
#         return self.group+"."+self.name if self.name else self.group

#     def serialize(self):
#         return self.serializer.serialize(self.value)

#     def deserializeFrom(self, value):
#         self.value = self.serializer.deserialize(value)


# class RangeConfigItem(ConfigItem):
#     """ Config item of range """

#     @property
#     def range(self):
#         """ get the available range of config """
#         return self.validator.range


# class OptionsConfigItem(ConfigItem):
#     """ Config item with options """

#     @property
#     def options(self):
#         return self.validator.options


# class ColorConfigItem(ConfigItem):
#     """ Color config item """

#     def __init__(self, group: str, name: str, default, restart=False):
#         super().__init__(group, name, QColor(default),
#                          ColorValidator(default), ColorSerializer(), restart)


# class Config(Singleton, QObject):
#     """ Config of app """

#     # folders
#     musicFolders = ConfigItem(
#         "Folders", "LocalMusic", [], FolderListValidator())
#     downloadFolder = ConfigItem(
#         "Folders", "Download", QStandardPaths.writableLocation(QStandardPaths.MusicLocation), FolderValidator())
#     cacheFolder = ConfigItem(
#         "Folders", "CacheFolder", Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation))/APP_NAME, FolderValidator(), restart=True)

#     onlinePageSize = RangeConfigItem(
#         "Online", "PageSize", 30, RangeValidator(0, 50))

#     # main window
#     enableAcrylicBackground = ConfigItem(
#         "MainWindow", "EnableAcrylicBackground", False, BoolValidator())
#     minimizeToTray = ConfigItem(
#         "MainWindow", "MinimizeToTray", True, BoolValidator())
#     playBarColor = ColorConfigItem("MainWindow", "PlayBarColor", "#225C7F")
#     themeMode = OptionsConfigItem(
#         "MainWindow", "ThemeMode", Theme.AUTO, OptionsValidator(Theme), EnumSerializer(Theme), restart=True)
#     recentPlaysNumber = RangeConfigItem(
#         "MainWindow", "RecentPlayNumbers", 300, RangeValidator(10, 300))
#     dpiScale = OptionsConfigItem(
#         "MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
#     language = OptionsConfigItem(
#         "MainWindow", "Language", Language.AUTO, OptionsValidator(Language), EnumSerializer(Language), restart=True)

#     # media player
#     randomPlay = ConfigItem("Player", "RandomPlay", False, BoolValidator())
#     playerVolume = RangeConfigItem(
#         "Player", "Volume", 30, RangeValidator(0, 100))
#     playerMuted = ConfigItem("Player", "Muted", False, BoolValidator())
#     playerPosition = RangeConfigItem(
#         "Player", "Position", 0, RangeValidator(0, float("inf")))
#     playerSpeed = RangeConfigItem(
#         "Player", "Speed", 1, RangeValidator(0.1, float("inf")))

#     # playing interface
#     lyricFontSize = RangeConfigItem(
#         "PlayingInterface", "LyricFontSize", 24, RangeValidator(10, 40))
#     lyricFontFamily = ConfigItem(
#         "PlayingInterface", "LyricFontFamily", "Microsoft YaHei")
#     albumBlurRadius = RangeConfigItem(
#         "PlayingInterface", "AlbumBlurRadius", 12, RangeValidator(0, 40))

#     # desktop lyric
#     deskLyricFontColor = ColorConfigItem("DesktopLyric", "FontColor", Qt.white)
#     deskLyricHighlightColor = ColorConfigItem(
#         "DesktopLyric", "HighlightColor", "#0099BC")
#     deskLyricFontSize = RangeConfigItem(
#         "DesktopLyric", "FontSize", 50, RangeValidator(15, 50))
#     deskLyricStrokeSize = RangeConfigItem(
#         "DesktopLyric", "StrokeSize", 5, RangeValidator(0, 20))
#     deskLyricStrokeColor = ColorConfigItem(
#         "DesktopLyric", "StrokeColor", Qt.black)
#     deskLyricFontFamily = ConfigItem(
#         "DesktopLyric", "FontFamily", "Microsoft YaHei")
#     deskLyricAlignment = OptionsConfigItem(
#         "DesktopLyric", "Alignment", "Center", OptionsValidator(["Center", "Left", "Right"]))

#     # embedded lyrics
#     preferEmbedLyric = ConfigItem(
#         "EmbeddedLyric", "PreferEmbedded", True, BoolValidator())
#     embedLyricWhenSave = ConfigItem(
#         "EmbeddedLyric", "EmbedWhenSave", False, BoolValidator())    # embed lyric when saving song info

#     # software update
#     checkUpdateAtStartUp = ConfigItem(
#         "Update", "CheckUpdateAtStartUp", True, BoolValidator())

#     appRestartSig = pyqtSignal()

#     def __init__(self):
#         super().__init__()
#         self.__theme = Theme.LIGHT
#         self.load()

#     def get(self, item: ConfigItem):
#         return item.value

#     def set(self, item: ConfigItem, value):
#         if item.value == value:
#             return

#         item.value = value
#         self.save()

#         if item.restart:
#             self.appRestartSig.emit()

#     @classmethod
#     def toDict(cls, serialize=True):
#         """ convert config items to `dict` """
#         items = {}
#         for name in dir(cls):
#             item = getattr(cls, name)
#             if not isinstance(item, ConfigItem):
#                 continue

#             value = item.serialize() if serialize else item.value
#             if not items.get(item.group):
#                 if not item.name:
#                     items[item.group] = value
#                 else:
#                     items[item.group] = {}

#             if item.name:
#                 items[item.group][item.name] = value

#         return items

#     @classmethod
#     def save(cls):
#         CONFIG_FOLDER.mkdir(parents=True, exist_ok=True)
#         with open(CONFIG_FILE, "w", encoding="utf-8") as f:
#             json.dump(cls.toDict(), f, ensure_ascii=False, indent=4)

#     @exceptionHandler("config")
#     def load(self):
#         """ load config """
#         try:
#             with open(CONFIG_FILE, encoding="utf-8") as f:
#                 cfg = json.load(f)
#         except:
#             cfg = {}

#         # map config items'key to item
#         items = {}
#         for name in dir(Config):
#             item = getattr(Config, name)
#             if isinstance(item, ConfigItem):
#                 items[item.key] = item

#         # update the value of config item
#         for k, v in cfg.items():
#             if not isinstance(v, dict) and items.get(k) is not None:
#                 items[k].deserializeFrom(v)
#             elif isinstance(v, dict):
#                 for key, value in v.items():
#                     key = k + "." + key
#                     if items.get(key) is not None:
#                         items[key].deserializeFrom(value)

#         if sys.platform != "win32":
#             self.enableAcrylicBackground.value = False

#         if self.get(self.themeMode) == Theme.AUTO:
#             theme = darkdetect.theme()
#             if theme:
#                 self.__theme = Theme(theme)
#             else:
#                 self.__theme = Theme.LIGHT
#         else:
#             self.__theme = self.get(self.themeMode)

#     @property
#     def theme(self) -> Theme:
#         """ theme mode, could be `Theme.LIGHT` or `Theme.DARK` """
#         return self.__theme

#     @property
#     def lyricFont(self):
#         """ get the playing interface lyric font """
#         font = QFont(self.lyricFontFamily.value)
#         font.setPixelSize(self.lyricFontSize.value)
#         return font

#     @lyricFont.setter
#     def lyricFont(self, font: QFont):
#         dpi = QGuiApplication.primaryScreen().logicalDotsPerInch()
#         self.lyricFontFamily.value = font.family()
#         self.lyricFontSize.value = max(10, int(font.pointSize()*dpi/72))
#         self.save()

#     @property
#     def desktopLyricFont(self):
#         """ get the desktop lyric font """
#         font = QFont(self.deskLyricFontFamily.value)
#         font.setPixelSize(self.deskLyricFontSize.value)
#         return font

#     @desktopLyricFont.setter
#     def desktopLyricFont(self, font: QFont):
#         dpi = QGuiApplication.primaryScreen().logicalDotsPerInch()
#         self.deskLyricFontFamily.value = font.family()
#         self.deskLyricFontSize.value = max(15, int(font.pointSize()*dpi/72))
#         self.save()


# config = Config()
