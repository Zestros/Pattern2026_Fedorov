from Src.Core.abstract_dto import abstract_dto
from Src.Core.filter_criteria import sort_direction_enum
from Src.Dtos.filter_item_dto import filter_item_dto


class sort_item_dto(abstract_dto):
    """Сортировка по одному полю."""

    # Путь к полю относительно исходной модели.
    field: str
    # Направление сортировки по этому полю.
    direction: sort_direction_enum = sort_direction_enum.ASC


class filter_dto(abstract_dto):
    """Общие параметры отбора и сортировки."""

    # Условия, которые должны выполняться одновременно.
    filters: tuple[filter_item_dto, ...] = ()
    # Поля сортировки в порядке приоритета.
    sort: tuple[sort_item_dto, ...] = ()
