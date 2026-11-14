from inspect import getattr_static
from types import UnionType
from typing import get_args, get_origin, get_type_hints

from Src.Core.abstract_entity_repository import abstract_entity_repository
from Src.Core.abstract_model import abstract_model
from Src.Core.abstract_recipe_component import abstract_recipe_component
from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.recipe_model import recipe_model
from Src.Models.unit_model import unit_model
from Src.Models.warehouse_model import warehouse_model


class entity_type_adapter:
    """Преобразует имена ресурсов и JSON между HTTP и доменными моделями."""

    __models = {
        "group": group_model,
        "item": item_model,
        "recipe": recipe_model,
        "unit": unit_model,
        "warehouse": warehouse_model,
    }

    @classmethod
    def resolve(cls, value: str) -> type[entity_model]:
        """Возвращает класс модели для параметра URL."""
        try:
            return cls.__models[value.strip().lower()]
        except KeyError as error:
            raise arguments_exception("entity_type", "Неизвестный тип сущности") from error

    def __init__(self, repository: abstract_entity_repository) -> None:
        """Получает репозиторий для разрешения связей по коду."""
        self.__repository = repository

    def create(self, model_type: type[entity_model], source: dict) -> entity_model:
        """Создаёт сущность из полей API, используя конструкторы и сеттеры моделей."""
        if model_type is item_model and "recipe" in source:
            model_type = recipe_item_model
        return self.__build(model_type, self.decode(model_type, source))

    def decode(self, model_type: type[abstract_model], source: object) -> dict[str, object]:
        """Определяет типы полей по аннотациям и разрешает вложенные значения."""
        model_type.validate_fields(source)
        computed = set(model_type.computed_fields)
        hints = get_type_hints(model_type.__init__)
        fields = {}
        for name, value in source.items():
            if name in computed:
                raise arguments_exception(name, "Расчётное поле нельзя изменить")
            if name == "unique_code" and isinstance(value, str):
                if any(char in value for char in "/\\") or value.strip() in {".", ".."} or not value.isprintable():
                    raise arguments_exception(name, "Код должен помещаться в один сегмент URL")
            hint = hints.get(name)
            if hint is None:
                descriptor = getattr_static(model_type, name, None)
                if isinstance(descriptor, property) and descriptor.fget is not None:
                    hint = get_type_hints(descriptor.fget).get("return")
            fields[name] = self.__decode_value(name, value, hint)
        return fields

    def __decode_value(self, field: str, value: object, hint: object) -> object:
        """Заменяет коды зарегистрированными сущностями и собирает вложенные модели."""
        options = get_args(hint) if get_origin(hint) is UnionType else (hint,)
        hint = next((option for option in options if option is not type(None)), None)
        if value is None:
            return None
        if hint is abstract_recipe_component:
            hint = item_model
        if isinstance(hint, type) and issubclass(hint, entity_model):
            if not isinstance(value, str) or not value.strip():
                raise arguments_exception(field, "Ожидается код связанной сущности")
            target = self.__repository.find(hint, value)
            if target is None:
                raise arguments_exception(field, f"Связанная сущность с кодом {value!r} не найдена")
            return target
        if isinstance(hint, type) and issubclass(hint, abstract_model):
            return self.__build(hint, self.decode(hint, value))
        if get_origin(hint) is tuple:
            if not isinstance(value, list):
                raise arguments_exception(field, "Ожидается JSON-массив")
            item_type, _ = get_args(hint)
            return [self.__decode_value(field, item, item_type) for item in value]
        return value

    @staticmethod
    def __build(model_type: type[abstract_model], fields: dict) -> abstract_model:
        """Проверяет обязательные поля и передаёт значения фабричному методу модели."""
        for name in model_type.constructor_fields(required_only=True):
            if name not in fields:
                raise arguments_exception(name, "Отсутствует обязательное поле")
        if issubclass(model_type, unit_model) and fields.get("base_unit") is None:
            # Фабричный метод принимает ссылку на выделяемую базовую единицу.
            instance = model_type.__new__(model_type)
            return model_type.from_fields({**fields, "base_unit": instance}, instance=instance)
        return model_type.from_fields(fields)

    @classmethod
    def encode(cls, model: abstract_model) -> dict[str, object]:
        """Возвращает поля модели, представляя связи с сущностями их кодами."""
        return {name: cls.__encode_value(getattr(model, name)) for name in model.field_names()}

    @classmethod
    def __encode_value(cls, value: object) -> object:
        """Разворачивает вложенное значение без повторной сериализации связанных сущностей."""
        if isinstance(value, entity_model):
            return value.unique_code
        if isinstance(value, abstract_model):
            return cls.encode(value)
        if isinstance(value, (list, tuple)):
            return [cls.__encode_value(item) for item in value]
        return value
