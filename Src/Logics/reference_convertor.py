from inspect import getattr_static
from types import ModuleType

from Src.Core.abstract_convertor import abstract_convertor
from Src.Dtos.conversion_context_dto import conversion_context_dto
from Src.Logics.basic_convertor import basic_convertor
from Src.Logics.datetime_convertor import datetime_convertor


class reference_convertor(abstract_convertor):
    """Преобразует поля моделей и коллекций, используя конверторы значений."""

    def __init__(self) -> None:
        """Создаёт обработчики простых значений и даты для полей объекта."""
        self.__basic_convertor = basic_convertor()
        self.__datetime_convertor = datetime_convertor()

    @staticmethod
    def can_convert(source: object) -> bool:
        """Принимает коллекции и экземпляры с атрибутами или свойствами."""
        if isinstance(source, (dict, list, tuple)):
            return True
        if isinstance(source, (type, ModuleType)) or callable(source):
            return False
        return hasattr(source, "__dict__") or any(
            not name.startswith("_")
            and isinstance(getattr_static(type(source), name), property)
            for name in dir(type(source))
        )

    def convert(
        self,
        source: object,
        field_name: str = "value",
        context: conversion_context_dto | None = None,
    ) -> dict[str, object]:
        """Преобразует составное значение с общей защитой от циклов."""
        return self._convert(source, field_name, context)

    @staticmethod
    def _get_fields(source: object) -> list[str]:
        """Находит публичные атрибуты и унаследованные свойства без их чтения."""
        names = {
            name for name in dir(type(source))
            if not name.startswith("_")
            and isinstance(getattr_static(type(source), name), property)
        }
        if hasattr(source, "__dict__"):
            names.update(
                name for name, value in vars(source).items()
                if not name.startswith("_") and not callable(value)
            )
        return sorted(names)

    def _convert_value(
        self, source: object, context: conversion_context_dto,
    ) -> object:
        """Сохраняет ключи словарей, порядок коллекций и имена полей объектов."""
        if isinstance(source, dict):
            return {
                key: self._convert_nested(value, str(key), context)
                for key, value in source.items()
            }
        if isinstance(source, (list, tuple)):
            return [
                self._convert_nested(value, str(index), context)
                for index, value in enumerate(source)
            ]
        return {
            name: self._convert_nested(getattr(source, name), name, context)
            for name in self._get_fields(source)
        }

    def _convert_nested(
        self, source: object, field_name: str, context: conversion_context_dto,
    ) -> object:
        """Обрабатывает простое поле, дату либо рекурсивно составное значение."""
        if self.__basic_convertor.can_convert(source):
            convertor = self.__basic_convertor
        elif self.__datetime_convertor.can_convert(source):
            convertor = self.__datetime_convertor
        else:
            convertor = self
        return convertor.convert(source, field_name, context)[field_name]
