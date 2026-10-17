from enum import Enum


class entity_type_enum(Enum):
    """Типы сущностей, доступные для отчётности."""

    ITEM = "item"
    UNIT = "unit"
    RECIPE = "recipe"
