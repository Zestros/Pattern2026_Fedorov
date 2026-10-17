from dataclasses import dataclass

from Src.Core.exception import arguments_exception


report_value = str | int | float | bool | None


@dataclass(frozen=True)
class report_data_dto:
    """Хранит поля и таблицу отчёта независимо от формата."""

    title: str
    fields: tuple[tuple[str, report_value], ...]
    columns: tuple[str, ...] = ()
    rows: tuple[tuple[report_value, ...], ...] = ()

    def __post_init__(self) -> None:
        """Проверяет соответствие строк объявленным столбцам."""
        if any(len(row) != len(self.columns) for row in self.rows):
            raise arguments_exception(
                "rows",
                "Количество значений строки должно совпадать с количеством столбцов",
            )


def format_report_value(value: report_value) -> str:
    """Представляет отсутствующее значение пустой строкой во всех форматах."""
    return "" if value is None else str(value)
