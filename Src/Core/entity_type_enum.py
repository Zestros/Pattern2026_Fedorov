from enum import Enum


class entity_type_enum(Enum):
    """Типы сущностей для чтения ранее сохранённых значений JSON."""

    ITEM = "item"
    UNIT = "unit"
    RECIPE = "recipe"
    GROUP = "group"
    WAREHOUSE = "warehouse"
