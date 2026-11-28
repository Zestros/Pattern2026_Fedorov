from functools import lru_cache
from inspect import getattr_static, getmembers_static
from typing import get_type_hints

from Src.Core.dto_field import dto_field


class abstract_dto:
    """Описывает поля DTO и учитывает явно переданные или присвоенные значения."""
    def __init__(self, **values: object) -> None:
        """Сохраняет только переданные поля, отличая пропуск значения от None."""
        allowed = {field.name for field in self.fields()}
        if any(name.startswith("_") or hasattr(abstract_dto, name) for name in allowed):
            raise TypeError("Поле DTO перекрывает служебный контракт")
        if values.keys() - allowed:
            raise TypeError("Неизвестные поля DTO")
        object.__setattr__(self, "_abstract_dto__provided", frozenset(values))
        for name, value in values.items():
            object.__setattr__(self, name, value)

    @classmethod
    @lru_cache(maxsize=None)
    def fields(cls) -> tuple[dto_field, ...]:
        """Возвращает кешированное описание аннотаций и свойств с сеттерами."""
        hints = get_type_hints(cls)
        for name, descriptor in getmembers_static(cls):
            if name.startswith("_") or not isinstance(descriptor, property) or descriptor.fset is None:
                continue
            hints[name] = get_type_hints(descriptor.fget)["return"]
        return tuple(dto_field(name, hint, cls) for name, hint in hints.items())

    def contains(self, name: str) -> bool:
        """Проверяет, было ли поле явно передано или присвоено."""
        return name in self.__provided

    def field_value(self, name: str) -> object:
        """Возвращает переданное значение или сообщает об отсутствии поля."""
        if not self.contains(name):
            raise KeyError(name)
        return getattr(self, name)

    def __setattr__(self, name: str, value: object) -> None:
        """Разрешает присваивание через явно объявленный сеттер DTO."""
        descriptor = getattr_static(type(self), name, None)
        if name.startswith("_") or not isinstance(descriptor, property) or descriptor.fset is None:
            raise AttributeError("Поле DTO доступно только для чтения")
        object.__setattr__(self, name, value)
        object.__setattr__(self, "_abstract_dto__provided", self.__provided | {name})

    def __delattr__(self, name: str) -> None:
        """Запрещает удаление полей в обход учёта их присутствия."""
        raise AttributeError("Удаление полей DTO запрещено")
