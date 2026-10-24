from Src.Core.abstract_convert_factory import abstract_convert_factory
from Src.Core.abstract_convertor import abstract_convertor
from Src.Core.exception import arguments_exception
from Src.Logics.basic_convertor import basic_convertor
from Src.Logics.datetime_convertor import datetime_convertor
from Src.Logics.reference_convertor import reference_convertor


class convert_factory(abstract_convert_factory):
    """Выбирает подходящий конвертор по типу переданного значения."""

    def __init__(self) -> None:
        """Создаёт поддерживаемые конверторы."""
        self.__convertors = [
            basic_convertor(),
            datetime_convertor(),
            reference_convertor(),
        ]

    def create(self, source: object) -> abstract_convertor:
        """Возвращает первый подходящий конвертор."""
        for convertor in self.__convertors:
            if convertor.can_convert(source):
                return convertor
        raise arguments_exception(
            "source", f"Тип {type(source).__name__} не поддерживается",
        )
