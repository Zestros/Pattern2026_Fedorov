from collections.abc import Callable
from datetime import date, datetime

from Src.Core.abstract_dto import abstract_dto
from Src.Core.field_path import field_path
from Src.Core.filter_operator_enum import filter_operator_enum
from Src.Core.validator import validator


class filter_item_dto(abstract_dto):
    """Одно условие фильтрации по пути к полю модели."""

    @property
    def field(self) -> str:
        """Возвращает путь к полю относительно исходной модели."""
        return self.__field

    @field.setter
    def field(self, value: str) -> None:
        """Сохраняет корректный путь из публичных имён."""
        field_path.validate(value)
        object.__setattr__(self, "_filter_item_dto__field", value)

    @property
    def operator(self) -> filter_operator_enum:
        """Возвращает операцию сравнения."""
        return self.__operator

    @operator.setter
    def operator(self, value: filter_operator_enum) -> None:
        """Проверяет, что передана известная операция сравнения."""
        validator.validate(value, filter_operator_enum, field="operator")
        object.__setattr__(self, "_filter_item_dto__operator", value)

    @property
    def value(self) -> str | date:
        """Возвращает текст или дату для сравнения."""
        return self.__value

    @value.setter
    def value(self, value: str | date) -> None:
        """Проверяет непустой текст или дату и сохраняет значение."""
        validator.validate(value, (str, date), field="value")
        object.__setattr__(self, "_filter_item_dto__value", value)

    def matches(self, model: object, path: field_path, compare: Callable) -> bool:
        """Сравнивает значения пути, переводя время движения в календарную дату."""
        expected = self.value
        for value in path.values(model):
            if isinstance(expected, date) and isinstance(value, datetime):
                value = value.date()
            if isinstance(value, self.operator.operand_type) and compare(value, expected):
                return True
        return False
