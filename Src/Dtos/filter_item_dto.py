from Src.Core.abstract_dto import abstract_dto
from Src.Core.filter_operator_enum import filter_operator_enum


class filter_item_dto(abstract_dto):
    """Одно условие фильтрации по пути к текстовому полю."""

    # Путь к полю относительно исходной модели.
    field: str
    # Способ сравнения.
    operator: filter_operator_enum
    # Текст для сравнения.
    value: str
