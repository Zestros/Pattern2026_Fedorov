from Src.Core.exception import arguments_exception


class report_field_dto:
    """Именованное текстовое поле подготовленного отчёта."""

    def __init__(self, name: str, value: str) -> None:
        """Сохраняет проверенные имя и текст поля."""
        self.__set_name(name)
        self.__set_value(value)

    def __set_name(self, value: str) -> None:
        """Проверяет тип и сохраняет подпись поля."""
        if not isinstance(value, str):
            raise arguments_exception("name", "Имя должно быть строкой")
        self.__name = value

    def __set_value(self, value: str) -> None:
        """Сохраняет текстовое значение, допуская пустую строку."""
        if not isinstance(value, str):
            raise arguments_exception("value", "Значение должно быть строкой")
        self.__value = value

    @property
    def name(self) -> str:
        """Возвращает подпись поля."""
        return self.__name

    @property
    def value(self) -> str:
        """Возвращает текстовое значение поля."""
        return self.__value

    def __iter__(self):
        """Предоставляет пару имя-значение для последовательного вывода."""
        return iter((self.name, self.value))
