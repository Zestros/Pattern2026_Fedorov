from Src.Core.abstract_model import abstract_model
from Src.Core.exception import  arguments_exception


class entity_model(abstract_model):
    """Базовая модель с уникальным кодом и наименованием."""

    "Наименование сущности."
    __name:str = ""

    @property
    def name(self) -> str:
        """Возвращает наименование сущности."""
        return self.__name

    @name.setter
    def name(self, value:str):
        """Устанавливает непустое наименование длиной до 50 символов."""
        if not isinstance(value, str):
            raise arguments_exception(
                "name",
                "Наименование должно быть строкой",
            )

        name = value.strip()

        if name == "":
            raise arguments_exception(
                "name",
                "Наименование не может быть пустым",
            )

        if len(name) > 50:
            raise arguments_exception(
                "name",
                "Наименование не может превышать 50 символов",
            )

        self.__name = name

  