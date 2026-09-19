from abc import ABC, abstractmethod
import uuid

class BaseClass(ABC):
    """Объект с уникальным идентификатором и именем."""

    def __init__(self):
        """Создаёт объект с уникальным идентификатором и именем."""
        self.__id = uuid.uuid4()
        self.__name = ""

    @property
    def get_id(self):
        """Возвращает идентификатор объекта."""
        return self.__id

    @property
    def get_name(self):
        """Возвращает имя объекта."""
        return self.__name
    
    def set_name(self, name):
        """Устанавливает новое имя объекта."""
        if not name:
            raise ValueError("Имя не может быть пустым")
        self.__name = name
