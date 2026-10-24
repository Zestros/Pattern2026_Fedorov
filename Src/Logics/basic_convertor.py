from Src.Core.abstract_convertor import abstract_convertor
from Src.Dtos.conversion_context_dto import conversion_context_dto


class basic_convertor(abstract_convertor):
    """Сохраняет числа, строки, логические значения и None без изменения типа."""

    @staticmethod
    def can_convert(source: object) -> bool:
        """Проверяет принадлежность к поддерживаемым простым типам."""
        return source is None or isinstance(source, (int, float, str, bool))

    def convert(
        self,
        source: object,
        field_name: str = "value",
        context: conversion_context_dto | None = None,
    ) -> dict[str, object]:
        """Возвращает простое значение под указанным именем поля."""
        return self._convert(source, field_name, context)

    def _convert_value(
        self, source: object, context: conversion_context_dto,
    ) -> object:
        """Возвращает простое значение без изменения."""
        return source
