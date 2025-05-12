# utils/singleton.py
from PyQt6.QtCore import QObject

class Singleton(type):
    """ Metaclass for creating singleton classes """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

def qsingleton(cls):
    """ Decorator for creating singleton QObject classes """
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

# --- Пример использования метакласса ---
# class MySingletonClass(metaclass=Singleton):
#     def __init__(self):
#         print("Initializing MySingletonClass")

# --- Пример использования декоратора для QObject ---
# @qsingleton
# class MyQObjectSingleton(QObject):
#     def __init__(self):
#         super().__init__()
#         print("Initializing MyQObjectSingleton")