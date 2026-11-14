from abc import ABC
from inspect import Parameter, getmembers_static, signature
from typing import Self
import uuid

from Src.Core.exception import arguments_exception
from Src.Core.model_fields import set_public_fields


class abstract_model(ABC):
    """Базовая модель с уникальным кодом и сравнением по этому коду."""

    # Уникальный код модели.
    __unique_code: str

    # Дополнительные поля, восстанавливаемые по правилам конкретной модели.
    state_fields: tuple[str, ...] = ()
    # Расчётные свойства, сохранённые в JSON для сверки после сборки графа.
    computed_fields: tuple[str, ...] = ()

    def __init__(self) -> None:
        """Создаёт уникальный код модели."""
        super().__init__()
        self.__unique_code = uuid.uuid4().hex

    @property
    def unique_code(self) -> str:
        """Возвращает уникальный код модели."""
        return self.__unique_code

    @unique_code.setter
    def unique_code(self, value: str) -> None:
        """Устанавливает непустой строковый уникальный код."""
        if not isinstance(value, str):
            raise arguments_exception(
                "unique_code",
                "Уникальный код должен быть строкой",
            )

        code = value.strip()

        if code == "":
            raise arguments_exception(
                "unique_code",
                "Уникальный код не может быть пустым",
            )

        self.__unique_code = code

    @classmethod
    def type_name(cls) -> str:
        """Возвращает полное имя класса вместе с модулем."""
        return f"{cls.__module__}.{cls.__qualname__}"

    @property
    def type(self) -> str:
        """Возвращает имя типа экземпляра."""
        return type(self).type_name()

    @classmethod
    def field_names(cls) -> tuple[str, ...]:
        """Находит свойства с сеттером или параметром конструктора без вызова геттеров."""
        constructor_fields = cls.constructor_fields()
        properties = {
            name for name, descriptor in getmembers_static(cls)
            if not name.startswith("_") and isinstance(descriptor, property)
            and descriptor.fget is not None
            and (descriptor.fset is not None or name in constructor_fields)
        }
        additional_fields = {
            name for base in cls.__mro__
            for name in base.__dict__.get("state_fields", ())
        }
        return tuple(sorted(properties | additional_fields | set(cls.computed_fields)))

    @classmethod
    def validate_fields(cls, fields: dict[str, object]) -> None:
        """Отклоняет поля вне контракта до создания или изменения модели."""
        if not isinstance(fields, dict):
            raise arguments_exception("fields", "Ожидается словарь полей")
        allowed = cls.field_names()
        for name in fields:
            if name not in allowed:
                raise arguments_exception(str(name), "Неизвестное поле модели")

    @classmethod
    def constructor_fields(cls, *, required_only: bool = False) -> tuple[str, ...]:
        """Возвращает имена именованных параметров, при необходимости только обязательных."""
        parameters = list(signature(cls.__init__).parameters.values())[1:]
        return tuple(
            parameter.name for parameter in parameters
            if parameter.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
            and (not required_only or parameter.default is Parameter.empty)
        )

    @classmethod
    def validate_restore_fields(cls, fields: dict[str, object]) -> None:
        """Проверяет состояние сохранённой модели до сборки связанного графа."""
        cls.validate_fields(fields)
        if "unique_code" not in fields:
            raise arguments_exception("unique_code", "В модели должен быть указан доменный код")
        for name in cls.constructor_fields(required_only=True):
            if name not in fields:
                raise arguments_exception(name, "Отсутствует обязательный параметр конструктора")

    @classmethod
    def initial_restore_fields(cls) -> tuple[str, ...]:
        """Возвращает поля конструктора и код для инициализации перед обходом связей."""
        return (*cls.constructor_fields(), "unique_code")

    @classmethod
    def from_fields(
        cls, fields: dict[str, object], *, instance: Self | None = None,
    ) -> Self:
        """Создаёт модель из полей или инициализирует ранее выделенный экземпляр."""
        cls.validate_fields(fields)
        if instance is None:
            instance = cls.__new__(cls)
        elif type(instance) is not cls:
            raise arguments_exception("instance", "Ожидается экземпляр создаваемого класса")

        arguments = {name: fields[name] for name in cls.constructor_fields() if name in fields}
        cls.__init__(instance, **arguments)
        remaining = {name: value for name, value in fields.items() if name not in arguments}
        if "unique_code" in remaining:
            instance.unique_code = remaining.pop("unique_code")
        if remaining:
            instance.apply_fields(remaining)
        return instance

    def apply_fields(self, fields: dict[str, object]) -> None:
        """Заполняет свойства, которые можно установить после конструктора."""
        self.validate_fields(fields)
        set_public_fields(self, fields)

    def check_computed_fields(self, fields: dict[str, object]) -> None:
        """Сверяет сохранённые расчётные значения с восстановленной моделью."""
        for name in self.computed_fields:
            if name in fields and getattr(self, name) != fields[name]:
                raise arguments_exception(name, "Расчётное поле не соответствует восстановленной модели")

    def __eq__(self, other):
        """Сравнивает модели по коду; прочие типы не поддерживает."""
        if not isinstance(other, abstract_model):
            return NotImplemented

        return self.unique_code == other.unique_code
