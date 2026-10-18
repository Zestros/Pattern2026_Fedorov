from typing import Any

from Src.Core.abstract_report_source import abstract_report_source
from Src.Core.abstract_report_source_factory import abstract_report_source_factory
from Src.Core.entity_type_enum import entity_type_enum
from Src.Core.validator import validator
from Src.Logics.item_report_source import item_report_source
from Src.Logics.unit_report_source import unit_report_source
from Src.Logics.recipe_report_source import recipe_report_source


class report_source_factory(abstract_report_source_factory):
    """Создаёт обработчики номенклатуры, единиц и рецептов."""

    def __init__(self) -> None:
        """Регистрирует обработчики поддерживаемых типов."""
        self.__mapping = {
            entity_type_enum.ITEM: item_report_source,
            entity_type_enum.UNIT: unit_report_source,
            entity_type_enum.RECIPE: recipe_report_source,
        }

    def create(self, entity_type: entity_type_enum) -> abstract_report_source[Any]:
        """Проверяет тип сущности и создаёт соответствующий обработчик."""
        validator.validate(entity_type, entity_type_enum, field="entity_type")
        return self.__mapping[entity_type]()
