from Src.Dtos.report_field_dto import report_field_dto
from Src.Dtos.report_row_dto import report_row_dto
from Src.Core.exception import arguments_exception


class report_data_dto:
    """Подготовленные данные отчёта: заголовок, именованные поля и таблица."""

    def __init__(self, title: str, fields: tuple, columns: tuple = (), rows: tuple = ()) -> None:
        """Проверяет структуру и сохраняет независимый снимок данных."""
        self.__set_title(title)
        self.__set_fields(fields)
        self.__set_table(columns, rows)

    def __set_title(self, value: str) -> None:
        """Сохраняет строковый заголовок, включая пустую строку."""
        if not isinstance(value, str):
            raise arguments_exception("title", "Ожидается строка")
        self.__title = value

    def __set_fields(self, fields: tuple) -> None:
        """Проверяет пары полей и сохраняет подготовленные DTO."""
        if not isinstance(fields, (tuple, list)):
            raise arguments_exception("fields", "Ожидается список или кортеж полей")
        prepared = []
        for field in fields:
            if not isinstance(field, (tuple, list, report_field_dto)) or len(tuple(field)) != 2:
                raise arguments_exception("fields", "Поле должно содержать имя и значение")
            name, value = field
            prepared.append(report_field_dto(name, format_report_value(value)))
        self.__fields = tuple(prepared)

    def __set_table(self, columns: tuple, rows: tuple) -> None:
        """Проверяет таблицу целиком и лишь затем сохраняет столбцы и строки."""
        if not isinstance(columns, (tuple, list)):
            raise arguments_exception("columns", "Ожидается список или кортеж столбцов")
        if any(not isinstance(name, str) for name in columns):
            raise arguments_exception("columns", "Названия столбцов должны быть строками")
        if not isinstance(rows, (tuple, list)):
            raise arguments_exception("rows", "Ожидается список или кортеж строк")
        prepared = []
        for row in rows:
            if not isinstance(row, (tuple, list, report_row_dto)):
                raise arguments_exception("rows", "Ожидается последовательность ячеек")
            if len(row) != len(columns):
                raise arguments_exception("rows", "Количество значений строки должно совпадать с количеством столбцов")
            prepared.append(report_row_dto(tuple(format_report_value(value) for value in row)))
        self.__columns = tuple(columns)
        self.__rows = tuple(prepared)

    @property
    def title(self) -> str:
        """Возвращает заголовок отчёта."""
        return self.__title

    @property
    def fields(self) -> tuple[report_field_dto, ...]:
        """Возвращает неизменяемую последовательность именованных полей."""
        return self.__fields

    @property
    def columns(self) -> tuple[str, ...]:
        """Возвращает названия столбцов в порядке вывода."""
        return self.__columns

    @property
    def rows(self) -> tuple[report_row_dto, ...]:
        """Возвращает строки таблицы в порядке вывода."""
        return self.__rows


def format_report_value(value: object) -> str:
    """Преобразует простое значение в текст; None означает пустую строку."""
    if value is not None and not isinstance(value, (str, int, float, bool)):
        raise arguments_exception("value", "Ожидается простое значение отчёта")
    return "" if value is None else str(value)
