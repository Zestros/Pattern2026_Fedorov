
class arguments_exception(Exception):
    """Ошибка аргумента с названием поля и описанием причины."""
    # Описание причины ошибки.
    __message: str = ""
    # Название некорректного аргумента.
    __field: str = ""
    # Переданная строка стека вызовов.
    __stack_trace: str = ""

    def __init__(self, field: str, message: str, stack_trace: str = ""):
        """Сохраняет сведения об ошибке, удаляя пробелы по краям."""
        self.__field = field.strip()
        self.__message = message.strip()
        self.__stack_trace = stack_trace.strip()

    def __str__(self):
        """Возвращает текст ошибки с полем, причиной и стеком вызовов."""
        return (
            f"Ошибка. Некорректный аргумент!\n"
            f"Поле: {self.__field}\n"
            f"{self.__message}\n"
            f"{self.__stack_trace}"
        )
