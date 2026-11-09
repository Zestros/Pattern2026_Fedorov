from abc import ABC
from inspect import Parameter, signature
from typing import Self
import uuid

from Src.Core.exception import arguments_exception
from Src.Core.model_fields import set_public_fields


class abstract_model(ABC):
    """Базовая модель с уникальным кодом и сравнением по этому коду."""

    # Уникальный код модели.
    __unique_code: str

    # Публичные поля состояния
    state_fields: tuple[str, ...] = ("unique_code",)

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
        """Объединяет явно объявленные поля модели и её предков."""
        return tuple(dict.fromkeys(
            name for base in reversed(cls.__mro__)
            for name in base.__dict__.get("state_fields", ())
        ))

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
    def constructor_fields(cls) -> tuple[str, ...]:
        """Возвращает имена параметров, которые конструктор принимает по ключу."""
        parameters = list(signature(cls.__init__).parameters.values())[1:]
        return tuple(
            parameter.name for parameter in parameters
            if parameter.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
        )

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
        instance.apply_fields(remaining)
        return instance

    def apply_fields(self, fields: dict[str, object]) -> None:
        """Заполняет свойства, которые можно установить после конструктора."""
        self.validate_fields(fields)
        set_public_fields(self, fields)

    def __eq__(self, other):
        """Сравнивает модели по коду; прочие типы не поддерживает."""
        if not isinstance(other, abstract_model):
            return NotImplemented

        return self.unique_code == other.unique_code
