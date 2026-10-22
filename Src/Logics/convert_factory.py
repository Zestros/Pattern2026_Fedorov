from Src.Core.abstract_convert_factory import abstract_convert_factory
from Src.Core.abstract_convertor import abstract_convertor
from Src.Dtos.conversion_context_dto import conversion_context_dto
from Src.Core.exception import arguments_exception
from Src.Logics.basic_convertor import basic_convertor
from Src.Logics.datetime_convertor import datetime_convertor
from Src.Logics.reference_convertor import reference_convertor


class convert_factory(abstract_convert_factory):
    """Выбирает конвертор и передаёт единый контекст всей операции."""

    def __init__(self) -> None:
        """Создаёт поддерживаемые конверторы."""
        self.__convertors = [
            basic_convertor(self),
            datetime_convertor(self),
            reference_convertor(self),
        ]

    def create(self, source: object) -> abstract_convertor:
        """Возвращает первый подходящий конвертор с обработчиком вложений."""
        for convertor in self.__convertors:
            if convertor.can_convert(source):
                return convertor
        raise arguments_exception(
            "source", f"Тип {type(source).__name__} не поддерживается",
        )

    def convert(
        self,
        source: object,
        field_name: str = "value",
        context: conversion_context_dto | None = None,
    ) -> dict[str, object]:
        """Создаёт контекст внешнего вызова или продолжает текущую операцию."""
        if context is None:
            context = conversion_context_dto()
        return self.create(source).convert(source, field_name, context)
