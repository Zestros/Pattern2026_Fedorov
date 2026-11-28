from datetime import date
from enum import Enum


class filter_operator_enum(Enum):
    """Операции сравнения текста и календарных дат."""

    # Полное совпадение.
    EQUALS = "EQUALS"
    # Вхождение подстроки без учёта регистра.
    LIKE = "LIKE"
    # Дата строго раньше границы.
    BEFORE = "BEFORE"
    # Дата не раньше границы.
    ON_OR_AFTER = "ON_OR_AFTER"
    # Дата не позже границы.
    ON_OR_BEFORE = "ON_OR_BEFORE"

    @property
    def operand_type(self) -> type:
        """Возвращает тип значения, которое принимает операция."""
        if self in (self.BEFORE, self.ON_OR_AFTER, self.ON_OR_BEFORE):
            return date
        return str
