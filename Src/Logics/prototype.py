from collections.abc import Iterable

from Src.Core.abstract_prototype import abstract_prototype
from Src.Core.filter_criteria import filter_criteria


class prototype(abstract_prototype):
    """Хранит коллекцию и клонирует её по переданным критериям."""

    def __init__(self, data: Iterable, criteria: filter_criteria) -> None:
        """Запоминает данные и правила их отбора и сортировки."""
        self.__data = tuple(data)
        self.__criteria = criteria

    @property
    def data(self) -> tuple:
        """Возвращает состав и порядок объектов этого экземпляра."""
        return self.__data

    def clone(self) -> "prototype":
        """Отбирает объекты, сортирует их и возвращает новый прототип."""
        selected = [
            model for model in self.__data
            if all(rule.matches(model) for rule in self.__criteria.filters)
        ]
        for rule in reversed(self.__criteria.sort):
            selected.sort(key=rule.key, reverse=rule.descending)
        return prototype(selected, self.__criteria)
