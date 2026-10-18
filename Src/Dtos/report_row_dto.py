from Src.Core.exception import arguments_exception


class report_row_dto:
    """Строка таблицы с неизменяемой последовательностью текстовых ячеек."""

    def __init__(self, values: tuple[str, ...]) -> None:
        """Проверяет значения и копирует последовательность ячеек."""
        self.__set_values(values)

    def __set_values(self, values: tuple[str, ...]) -> None:
        """Проверяет коллекцию и сохраняет независимый снимок ячеек."""
        if not isinstance(values, (tuple, list)):
            raise arguments_exception("values", "Ожидается список или кортеж ячеек")
        if any(not isinstance(value, str) for value in values):
            raise arguments_exception("values", "Ячейки должны быть строками")
        self.__values = tuple(values)

    @property
    def values(self) -> tuple[str, ...]:
        """Возвращает текст ячеек в порядке столбцов."""
        return self.__values

    def __iter__(self):
        """Перебирает ячейки строки."""
        return iter(self.values)

    def __len__(self) -> int:
        """Возвращает число ячеек."""
        return len(self.values)

    def __getitem__(self, index: int) -> str:
        """Возвращает ячейку по индексу столбца."""
        return self.values[index]
