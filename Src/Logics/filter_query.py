from collections.abc import Callable, Iterator, Mapping
from functools import lru_cache
from inspect import getattr_static
from types import UnionType
from typing import Union, get_args, get_origin, get_type_hints

from Src.Core.abstract_model import abstract_model
from Src.Core.exception import arguments_exception
from Src.Core.filter_criteria import filter_criteria, filter_item, sort_item
from Src.Core.filter_operator_enum import filter_operator_enum
from Src.Core.validator import validator
from Src.Dtos.filter_dto import filter_dto


class filter_query:
    """Преобразует DTO в готовые правила для прототипа по аннотациям моделей."""

    def __init__(self, models: tuple[type[abstract_model], ...],
                 operators: Mapping[filter_operator_enum, Callable]) -> None:
        """Получает зарегистрированные модели и доступные операции сравнения."""
        self.__models = models
        self.__operators = dict(operators)

    def prepare(self, model: type[abstract_model], criteria: filter_dto) -> filter_criteria:
        """Проверяет пути и связывает правила с операциями и значениями запроса."""
        filters = []
        for item in criteria.filters:
            path = self.__resolve(model, item.field)
            validator.validate(item.value, str, field="value")
            compare = self.__operators.get(item.operator)
            if compare is None:
                raise arguments_exception("operator", "Операция фильтрации недоступна")
            filters.append(filter_item(path, compare, item.value))

        sort = []
        for item in criteria.sort:
            path = self.__resolve(model, item.field)
            sort.append(sort_item(path, item.direction, ignore_case=path[-1] != "unique_code"))
        return filter_criteria(tuple(filters), tuple(sort))

    def __resolve(self, model: type[abstract_model], field: str) -> tuple[str, ...]:
        """Разрешает путь к имени или коду даже при пустой коллекции."""
        path = tuple(field.split("."))
        if path[-1] not in ("name", "unique_code"):
            raise arguments_exception("field", f"Недоступное поле: {field}")

        types = {model}
        for part in path:
            types = {
                field_type
                for model_type in types
                for field_type in self.__field_types(model_type, part)
            }
            if not types:
                break
        if str not in types:
            raise arguments_exception("field", f"Недоступное поле: {field}")
        return path

    def __field_types(self, model: type, name: str) -> Iterator[type]:
        """Ищет тип свойства также у зарегистрированных вариантов исходной модели."""
        yield from self.__value_types(self.__property_hint(model, name))
        for variant in self.__models:
            if variant is not model and issubclass(variant, model):
                yield from self.__value_types(self.__property_hint(variant, name))

    @staticmethod
    @lru_cache(maxsize=256)
    def __property_hint(model: type, name: str) -> object:
        """Читает тип публичного поля без обращения к экземплярам."""
        descriptor = getattr_static(model, name, None)
        if (issubclass(model, abstract_model) and isinstance(descriptor, property)
                and descriptor.fget is not None and name in model.field_names()):
            return get_type_hints(descriptor.fget).get("return")
        return None

    @staticmethod
    def __value_types(annotation: object) -> Iterator[type]:
        """Разворачивает параметры коллекций и объединений типов."""
        origin = get_origin(annotation)
        if origin in (list, tuple, Union, UnionType):
            for argument in get_args(annotation):
                yield from filter_query.__value_types(argument)
        elif isinstance(annotation, type) and annotation is not type(None):
            yield annotation
