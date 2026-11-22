from Src.Core.abstract_dto import abstract_dto
from Src.Core.field_path import field_path
from Src.Core.filter_operator_enum import filter_operator_enum
from Src.Core.validator import validator


class filter_item_dto(abstract_dto):
    """Одно условие фильтрации по пути к текстовому полю."""

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
    def value(self) -> str:
        """Возвращает текст, с которым сравнивается поле."""
        return self.__value

    @value.setter
    def value(self, value: str) -> None:
        """Проверяет непустой текст и сохраняет его для точного сравнения."""
        validator.validate(value, str, field="value")
        object.__setattr__(self, "_filter_item_dto__value", value)
