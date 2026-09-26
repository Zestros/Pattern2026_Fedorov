from abc import ABC
import uuid
from Src.Core.exception import  arguments_exception

"""
Абстрактный класс для наследования моделей
Содержит в себе только генерацию уникального кода
"""
class abstract_model(ABC):
    __unique_code:str

    def __init__(self) -> None:
        """Создает абстрактный класс для наследования моделей"""
        super().__init__()
        self.__unique_code = uuid.uuid4().hex

    """
    Уникальный код
    """
    @property
    def unique_code(self) -> str:
        return self.__unique_code
    
    @unique_code.setter
    def unique_code(self, value: str):
        """Устанавливает непустой строковый уникальный код."""
        if not isinstance(value, str):
            raise arguments_exception(
                "unique_code",
                "Уникальный код должен быть строкой",
            )

        code = value.strip()

        if code == "":
            raise arguments_exception(
                "unique_code",
                "Уникальный код не может быть пустым",
            )

        self.__unique_code = code

    def __eq__(self, other):
        """Сравнение моделей идет по id"""
        return self.__unique_code == other.__unique_code
