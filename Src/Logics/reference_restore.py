from Src.Core.exception import arguments_exception
from Src.Logics.Restore.graph_reader import graph_reader


class reference_restore:
    """Восстанавливает именованное значение из графа JSON с $id/$ref."""

    def restore(self, source: dict, field_name: str = "value") -> object:
        """Создаёт независимый читатель для одной операции восстановления."""
        if not isinstance(field_name, str) or not isinstance(source, dict):
            raise arguments_exception("source", "Ожидаются словарь и строковое имя поля")
        if set(source) != {field_name}:
            raise arguments_exception(field_name, "Ожидается одно именованное значение")
        try:
            return graph_reader().read(source[field_name])
        except (KeyError, TypeError, ValueError, AttributeError, RecursionError) as error:
            raise arguments_exception(field_name, f"Некорректные данные графа: {error}") from error
