from datetime import datetime

from Src.Core.abstract_restore_handler import abstract_restore_handler
from Src.Core.exception import arguments_exception


class datetime_restore(abstract_restore_handler):
    """Восстанавливает атомарный datetime с исходным смещением и fold."""

    # Имя типа и поля формата даты.
    type_name = "datetime"
    expected_fields = {"$type", "$value", "$fold"}

    def validate(self, node: dict) -> None:
        """Проверяет строку даты и допустимое значение fold."""
        super().validate(node)
        if not isinstance(node["$value"], str):
            raise arguments_exception("$value", "Ожидается строковое значение даты")
        if type(node["$fold"]) is not int or node["$fold"] not in (0, 1):
            raise arguments_exception("$fold", "Ожидается 0 или 1")

    def restore(self, instance: object, node: dict, reader) -> datetime:
        """Разбирает ISO 8601 и восстанавливает признак повторяющегося времени."""
        return datetime.fromisoformat(node["$value"]).replace(fold=node["$fold"])


class enum_restore(abstract_restore_handler):
    """Восстанавливает элемент явно зарегистрированного перечисления."""

    def __init__(self, enum_type) -> None:
        """Запоминает класс перечисления и его метаданные."""
        self.enum_type = enum_type
        self.type_name = enum_type.__name__
        self.expected_fields = {"$type", "$value"}

    def validate(self, node: dict) -> None:
        """Проверяет строковое имя элемента перечисления."""
        super().validate(node)
        if not isinstance(node["$value"], str):
            raise arguments_exception("$value", "Ожидается имя элемента перечисления")

    def restore(self, instance: object, node: dict, reader) -> object:
        """Возвращает существующий элемент перечисления по имени."""
        return self.enum_type[node["$value"]]
