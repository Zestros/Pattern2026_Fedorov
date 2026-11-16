from functools import lru_cache
from typing import get_type_hints


class dto_field:
    """Тип поля и простые правила его передачи и связывания."""
    def __init__(self, name: str, field_type: object, dto_type: type) -> None:
        """Читает правила поля из описания DTO с учётом наследования."""
        self.name = name
        self.type = field_type
        self.reference = None
        self.read_only = False
        self.optional = False
        for parent in reversed(dto_type.__mro__):
            self.reference = parent.__dict__.get("_references", {}).get(name, self.reference)
            self.read_only |= name in parent.__dict__.get("_read_only_fields", ())
            self.optional |= name in parent.__dict__.get("_optional_fields", ())


class abstract_dto:
    """Аннотации задают контракт; экземпляр хранит только переданные поля."""
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
        """Возвращает кешированное описание полей DTO по простым аннотациям."""
        return tuple(dto_field(name, hint, cls) for name, hint in get_type_hints(cls).items())

    def contains(self, name: str) -> bool:
        """Проверяет, было ли поле явно передано в DTO."""
        return name in self.__provided

    def field_value(self, name: str) -> object:
        """Возвращает переданное значение или сообщает об отсутствии поля."""
        if not self.contains(name):
            raise KeyError(name)
        return getattr(self, name)

    def __setattr__(self, name: str, value: object) -> None:
        """Запрещает изменение полей после создания согласованного DTO."""
        raise AttributeError("DTO неизменяем: создайте новый экземпляр")

    def __delattr__(self, name: str) -> None:
        """Запрещает удаление полей в обход учёта их присутствия."""
        raise AttributeError("DTO неизменяем: создайте новый экземпляр")
