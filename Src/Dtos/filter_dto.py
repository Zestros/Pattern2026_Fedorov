from Src.Core.abstract_dto import abstract_dto
from Src.Core.validator import validator
from Src.Dtos.filter_item_dto import filter_item_dto
from Src.Dtos.sort_item_dto import sort_item_dto


class filter_dto(abstract_dto):
    """Общие параметры отбора и сортировки."""

    # Оба списка можно опустить в запросе.
    _optional_fields = ("filters", "sort")
    # Условия по умолчанию отсутствуют.
    __filters = ()
    # Приоритеты сортировки по умолчанию отсутствуют.
    __sort = ()

    @property
    def filters(self) -> tuple[filter_item_dto, ...]:
        """Возвращает условия, которые должны выполняться одновременно."""
        return self.__filters

    @filters.setter
    def filters(self, value: tuple[filter_item_dto, ...]) -> None:
        """Проверяет тип каждого условия и сохраняет кортеж."""
        validator.validate(value, (tuple, list), field="filters")
        for item in value:
            validator.validate(item, filter_item_dto, field="filters")
        object.__setattr__(self, "_filter_dto__filters", tuple(value))

    @property
    def sort(self) -> tuple[sort_item_dto, ...]:
        """Возвращает правила сортировки в порядке приоритета."""
        return self.__sort

    @sort.setter
    def sort(self, value: tuple[sort_item_dto, ...]) -> None:
        """Проверяет тип каждого правила и сохраняет кортеж."""
        validator.validate(value, (tuple, list), field="sort")
        for item in value:
            validator.validate(item, sort_item_dto, field="sort")
        object.__setattr__(self, "_filter_dto__sort", tuple(value))
