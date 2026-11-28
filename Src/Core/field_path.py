from collections.abc import Iterator
from functools import lru_cache
from inspect import getattr_static
from types import UnionType
from typing import Union, get_args, get_origin, get_type_hints

from Src.Core.abstract_model import abstract_model
from Src.Core.exception import arguments_exception
from Src.Core.validator import validator


class field_path:
    """Проверяет вложенные пути по типам моделей и читает их значения."""

    def __init__(self, parts: tuple[str, ...], is_collection: bool) -> None:
        """Запоминает сегменты пути и наличие коллекции на пути."""
        self.__parts = parts
        self.__is_collection = is_collection

    @property
    def is_collection(self) -> bool:
        """Показывает, может ли путь проходить через коллекцию."""
        return self.__is_collection

    @staticmethod
    def validate(value: str) -> None:
        """Принимает последовательность публичных имён, разделённых точками."""
        validator.validate(value, str, field="field")
        if any(not part.isidentifier() or part.startswith("_") for part in value.split(".")):
            raise arguments_exception("field", "Ожидается путь из публичных имён полей")

    def values(self, model: object) -> Iterator[object]:
        """Читает вложенные значения, разворачивая коллекции и пропуская None."""
        pending = [(model, 0)]
        collections = {}
        while pending:
            value, index = pending.pop()
            if isinstance(value, (list, tuple)):
                key = (id(value), index)
                if key not in collections:
                    collections[key] = value
                    pending.extend((item, index) for item in reversed(value))
            elif value is not None:
                if index == len(self.__parts):
                    yield value
                else:
                    pending.append((getattr(value, self.__parts[index], None), index + 1))

    @classmethod
    def resolve(
        cls, model: type[abstract_model], field: str, variants: tuple[type[abstract_model], ...],
        *, value_type: type = str,
    ) -> "field_path":
        """Проверяет сегменты пути и ожидаемый тип конечного значения."""
        parts = tuple(field.split("."))
        if value_type is str and parts[-1] not in ("name", "unique_code"):
            raise arguments_exception("field", f"Недоступное поле: {field}")

        candidates = {(model, False)}
        for part in parts:
            candidates = {
                (field_type, through_collection or is_collection)
                for model_type, through_collection in candidates
                for field_type, is_collection in cls.__field_types(model_type, part, variants)
            }
            if not candidates:
                break
        matches = {is_collection for field_type, is_collection in candidates if issubclass(field_type, value_type)}
        if not matches:
            raise arguments_exception("field", f"Недоступное поле: {field}")
        return cls(parts, True in matches)

    @classmethod
    def __field_types(
        cls, model: type, name: str, variants: tuple[type[abstract_model], ...],
    ) -> Iterator[tuple[type, bool]]:
        """Читает тип свойства также у зарегистрированных вариантов модели."""
        yield from cls.__value_types(cls.__property_hint(model, name))
        for variant in variants:
            if variant is not model and issubclass(variant, model):
                yield from cls.__value_types(cls.__property_hint(variant, name))

    @staticmethod
    @lru_cache(maxsize=256)
    def __property_hint(model: type, name: str) -> object:
        """Читает тип публичного поля без обращения к экземплярам."""
        descriptor = getattr_static(model, name, None)
        if (issubclass(model, abstract_model) and isinstance(descriptor, property)
                and descriptor.fget is not None and name in model.field_names()):
            return get_type_hints(descriptor.fget).get("return")
        return None

    @classmethod
    def __value_types(cls, annotation: object, is_collection: bool = False) -> Iterator[tuple[type, bool]]:
        """Разворачивает коллекции и объединения, отмечая типы элементов коллекций."""
        origin = get_origin(annotation)
        if origin in (list, tuple, Union, UnionType):
            for argument in get_args(annotation):
                yield from cls.__value_types(argument, is_collection or origin in (list, tuple))
        elif isinstance(annotation, type) and annotation is not type(None):
            yield annotation, is_collection
