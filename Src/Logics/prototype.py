from collections.abc import Callable, Iterable, Mapping

from Src.Core.abstract_model import abstract_model
from Src.Core.abstract_prototype import abstract_prototype
from Src.Core.exception import arguments_exception
from Src.Core.field_path import field_path
from Src.Core.filter_operator_enum import filter_operator_enum
from Src.Dtos.filter_dto import filter_dto


class prototype(abstract_prototype):
    """Клонирует коллекцию с фильтрацией и сортировкой по DTO запроса."""

    def __init__(
        self, data: Iterable, criteria: filter_dto, model_type: type[abstract_model], *,
        model_types: tuple[type[abstract_model], ...], operators: Mapping[filter_operator_enum, Callable],
    ) -> None:
        """Запоминает коллекцию, DTO и настройки проверки и сравнения полей."""
        self.__data = tuple(data)
        self.__criteria = criteria
        self.__model_type = model_type
        self.__model_types = model_types
        self.__operators = operators

    @property
    def data(self) -> tuple:
        """Возвращает состав и порядок объектов этого экземпляра."""
        return self.__data

    def clone(self) -> "prototype":
        """Применяет все условия, затем стабильно сортирует отобранные объекты."""
        selected = list(self.__data)
        for item in self.__criteria.filters:
            value_type = item.operator.operand_type
            if type(item.value) is not value_type:
                raise arguments_exception("value", "Значение не соответствует операции фильтрации")
            path = field_path.resolve(self.__model_type, item.field, self.__model_types, value_type=value_type)
            compare = self.__operators.get(item.operator)
            if compare is None:
                raise arguments_exception("operator", "Операция фильтрации недоступна")
            selected = [model for model in selected if item.matches(model, path, compare)]

        for item in reversed(self.__criteria.sort):
            path = field_path.resolve(self.__model_type, item.field, self.__model_types)
            item.apply(selected, path)

        return prototype(
            selected, self.__criteria, self.__model_type,
            model_types=self.__model_types, operators=self.__operators,
        )
