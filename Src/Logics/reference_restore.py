import json
from enum import Enum
from inspect import getattr_static
from types import UnionType
from typing import Union, get_args, get_origin, get_type_hints
from uuid import uuid4

from Src.Core.abstract_model import abstract_model
from Src.Core.exception import arguments_exception
from Src.Logics.Restore.graph_reader import graph_reader


class reference_restore:
    """Восстанавливает именованное значение из графа JSON с $id/$ref."""

    @staticmethod
    def read_json(file_name: str) -> object:
        """Читает JSON из файла в UTF-8 перед восстановлением моделей."""
        with open(file_name, encoding="utf-8") as file:
            return json.load(file)

    def restore(self, source: dict, field_name: str = "value") -> object:
        """Создаёт независимый читатель для одной операции восстановления."""
        if not isinstance(field_name, str) or not isinstance(source, dict):
            raise arguments_exception("source", "Ожидаются словарь и строковое имя поля")
        if set(source) != {field_name}:
            raise arguments_exception(field_name, "Ожидается одно именованное значение")
        try:
            return graph_reader().read(source[field_name])
        except (KeyError, TypeError, ValueError, AttributeError, RecursionError) as error:
            raise arguments_exception(field_name, f"Некорректные данные графа: {error}") from error

    def restore_model(self, source: dict, model_type: type[abstract_model]) -> abstract_model:
        """Восстанавливает модель из обычного JSON, выводя типы полей из аннотаций."""
        result = self.restore({"value": self._model_node(source, model_type)})
        if not isinstance(result, model_type):
            raise arguments_exception("source", "Восстановленная модель имеет неверный тип")
        return result

    def _model_node(self, source: object, model_type: type[abstract_model]) -> dict:
        """Описывает узел модели для общего читателя графа."""
        if not isinstance(source, dict):
            raise arguments_exception(model_type.__name__, "Ожидается JSON-объект с полями модели")
        model_type.validate_fields(source)
        constructor_hints = get_type_hints(model_type.__init__)
        fields = {}
        for name, value in source.items():
            hint = constructor_hints.get(name)
            descriptor = getattr_static(model_type, name, None)
            if hint is None and isinstance(descriptor, property) and descriptor.fget is not None:
                hint = get_type_hints(descriptor.fget).get("return")
            fields[name] = self._typed_value(name, value, hint)
        fields.setdefault("unique_code", uuid4().hex)
        return {"$id": uuid4().hex, "$type": model_type.type_name(), "$fields": fields}

    def _typed_value(self, name: str, value: object, hint: object) -> object:
        """Описывает вложенную модель или значение перечисления по типу поля."""
        if value is None:
            return None
        options = get_args(hint) if get_origin(hint) in (Union, UnionType) else (hint,)
        if isinstance(value, dict):
            models = [kind for kind in options if isinstance(kind, type) and issubclass(kind, abstract_model)]
            if len(models) == 1:
                return self._model_node(value, models[0])
            raise arguments_exception(name, "Тип вложенной модели должен определяться однозначно")
        enums = [kind for kind in options if isinstance(kind, type) and issubclass(kind, Enum)]
        if not enums:
            return value
        if len(enums) != 1 or not isinstance(value, str):
            raise arguments_exception(name, "Ожидается строковое имя элемента перечисления")
        enum_type = enums[0]
        member = value.strip()
        if member not in enum_type.__members__:
            member = member.upper()
        if member not in enum_type.__members__:
            raise arguments_exception(name, f"Неизвестное значение: {value}")
        return {"$type": enum_type.__name__, "$value": member}
