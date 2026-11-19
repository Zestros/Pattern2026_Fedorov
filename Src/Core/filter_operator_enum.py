from enum import Enum


class filter_operator_enum(Enum):
    """Операции сравнения текстовых полей."""

    # Полное совпадение.
    EQUALS = "EQUALS"
    # Вхождение подстроки без учёта регистра.
    LIKE = "LIKE"
