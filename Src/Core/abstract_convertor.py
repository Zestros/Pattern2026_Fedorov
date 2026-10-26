from __future__ import annotations

from abc import ABC, abstractmethod

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
        """Проверяет аргументы, передаёт контекст и очищает его при ошибке."""
        if not isinstance(field_name, str):
            raise arguments_exception("field_name", "Имя поля должно быть строкой")
        if not self.can_convert(source):
            raise arguments_exception(
                field_name, f"Тип {type(source).__name__} не поддерживается конвертором",
            )

        if context is None:
            context = conversion_context_dto()
        is_root = not context.path
        context.path.append(field_name)
        try:
            return {field_name: self._convert_value(source, context)}
        except Exception:
            if is_root:
                context.object_ids.clear()
                context.objects.clear()
            raise
        finally:
            context.path.pop()

    @abstractmethod
    def _convert_value(
        self, source: object, context: conversion_context_dto,
    ) -> object:
        """Преобразует значение средствами конкретного конвертора."""
        pass
