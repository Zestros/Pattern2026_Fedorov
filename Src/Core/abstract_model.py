from abc import ABC
import uuid

from Src.Core.exception import arguments_exception


class abstract_model(ABC):
    """Базовая модель с уникальным кодом и сравнением по этому коду."""

    # Уникальный код модели.
    __unique_code: str

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

    def __eq__(self, other):
        """Сравнивает модели по коду; прочие типы не поддерживает."""
        if not isinstance(other, abstract_model):
            return NotImplemented

        return self.unique_code == other.unique_code
