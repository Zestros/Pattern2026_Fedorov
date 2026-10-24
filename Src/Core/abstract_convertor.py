from __future__ import annotations

from abc import ABC, abstractmethod

from Src.Core.abstract_model import abstract_model
from Src.Core.exception import arguments_exception
from Src.Dtos.conversion_context_dto import conversion_context_dto


class abstract_convertor(ABC):
    """Задаёт контракт конвертора и общий механизм рекурсивного обхода."""

    @staticmethod
    @abstractmethod
    def can_convert(source: object) -> bool:
        """Определяет, поддерживается ли значение этим конвертором."""
        pass

    @abstractmethod
    def convert(
        self,
        source: object,
        field_name: str = "value",
        context: conversion_context_dto | None = None,
    ) -> dict[str, object]:
        """Возвращает словарь с именем поля и преобразованным значением."""
        pass

    def _convert(
        self,
        source: object,
        field_name: str,
        context: conversion_context_dto | None,
    ) -> dict[str, object]:
        """Проверяет аргументы, ограничивает циклы и очищает путь при выходе."""
        if not isinstance(field_name, str):
            raise arguments_exception("field_name", "Имя поля должно быть строкой")
        if not self.can_convert(source):
            raise arguments_exception(
                field_name, f"Тип {type(source).__name__} не поддерживается конвертором",
            )

        if context is None:
            context = conversion_context_dto()
        object_id = id(source)
        if object_id in context.active_ids:
            if isinstance(source, abstract_model):
                return {field_name: None}
            raise arguments_exception(
                ".".join([*context.path, field_name]),
                "Циклическая ссылка на объект без уникального кода",
            )

        context.active_ids.add(object_id)
        context.path.append(field_name)
        try:
            return {field_name: self._convert_value(source, context)}
        finally:
            context.path.pop()
            context.active_ids.remove(object_id)

    @abstractmethod
    def _convert_value(
        self, source: object, context: conversion_context_dto,
    ) -> object:
        """Преобразует значение средствами конкретного конвертора."""
        pass
