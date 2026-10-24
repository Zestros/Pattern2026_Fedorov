from datetime import datetime

from Src.Core.abstract_convertor import abstract_convertor
from Src.Dtos.conversion_context_dto import conversion_context_dto


class datetime_convertor(abstract_convertor):
    """Преобразует дату и время в строку ISO 8601 с исходным смещением."""

    @staticmethod
    def can_convert(source: object) -> bool:
        """Проверяет, является ли значение датой и временем."""
        return isinstance(source, datetime)

    def convert(
        self,
        source: object,
        field_name: str = "value",
        context: conversion_context_dto | None = None,
    ) -> dict[str, object]:
        """Возвращает ISO-представление, сохраняя микросекунды и часовой пояс."""
        return self._convert(source, field_name, context)

    def _convert_value(
        self, source: object, context: conversion_context_dto,
    ) -> str:
        """Формирует строку ISO 8601 для проверенной даты."""
        return source.isoformat()
