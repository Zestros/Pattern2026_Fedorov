from Src.Core.entity_model import entity_model
from Src.Core.validator import validator

class report_result_dto(entity_model):
    """Модель для хранения результата формирования отчета"""
    __text:str = ""
    __binary:list

    def __init__(self, text: str = "", binary: list = None) -> None:
        if binary is None:
            binary = []
            
        self.__text = text
        self.__binary = binary


    @property
    def text(self) -> str:
        """Текстовый результат"""
        return self.__text

    @property
    def binary(self) -> list:
        return self.__binary

    @text.setter
    def text(self, value:str) -> None:
        validator.validate(value, str)
        self.__text = value
        self.__binary = []

    @binary.setter
    def binary(self, value:list) -> None:
        validator.validate(value, list)
        self.__binary = value
        self.__text = ""