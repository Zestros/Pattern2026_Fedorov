from enum import Enum
import math
from types import UnionType
from typing import get_args, get_origin
from Src.Core.abstract_dto import abstract_dto
from Src.Core.exception import arguments_exception


class dto_serializer:
    """Проверяет и преобразует внешние данные по единому контракту DTO."""
    def deserialize(self, source: object, target: type[abstract_dto], *, partial: bool = False) -> abstract_dto:
        """Проверяет контракт. Для PATCH пропуск поля сохраняется; вложенный объект полный."""
        if not isinstance(source, dict):
            raise arguments_exception("body", "Ожидается JSON-объект")
        fields = {field.name: field for field in target.fields()}
        for name in source:
            if name not in fields or fields[name].read_only:
                raise arguments_exception(str(name), "Неизвестное или расчётное поле")
        values = {}
        for name, field in fields.items():
            if name not in source:
                if not partial and not field.read_only and not field.optional and not hasattr(target, name):
                    raise arguments_exception(name, "Отсутствует обязательное поле")
                continue
            value = self.__decode(source[name], field.type, name)
            if value is not None and (field.reference is not None or name == "unique_code"):
                if not value.strip() or any(char in value for char in ("/", chr(92))) or value.strip() in {".", ".."} or not value.isprintable():
                    raise arguments_exception(name, "Некорректный код сущности")
                value = value.strip()
            values[name] = value
        return target(**values)

    def __decode(self, value: object, expected: object, name: str) -> object:
        """Проверяет тип значения и разбирает вложенный DTO либо коллекцию."""
        options = get_args(expected) if get_origin(expected) is UnionType else (expected,)
        if value is None and type(None) in options:
            return None
        for option in options:
            if isinstance(option, type) and issubclass(option, abstract_dto) and isinstance(value, dict):
                return self.deserialize(value, option)
            if isinstance(option, type) and issubclass(option, Enum) and isinstance(value, str):
                if value in option.__members__:
                    return option[value]
            if get_origin(option) is tuple and isinstance(value, list):
                return tuple(self.__decode(item, get_args(option)[0], name) for item in value)
            if option in (str, bool, int, float) and type(value) is option:
                if option is float and not math.isfinite(value):
                    break
                return value
        raise arguments_exception(name, "Значение не соответствует типу поля DTO")

    def serialize(self, source: object) -> object:
        """Одинаково обрабатывает DTO, коллекции и простые ответы API."""
        if isinstance(source, abstract_dto):
            return {field.name: self.serialize(source.field_value(field.name))
                    for field in source.fields() if source.contains(field.name)}
        if isinstance(source, Enum):
            return source.name
        if isinstance(source, (tuple, list)):
            return [self.serialize(item) for item in source]
        if source is None or type(source) in (str, int, float, bool):
            return source
        raise arguments_exception("source", "Для сериализации требуется DTO или простое значение")
