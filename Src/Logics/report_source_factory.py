from typing import Any

from Src.Core.abstract_report_source import abstract_report_source
from Src.Core.abstract_report_source_factory import abstract_report_source_factory
from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Logics.item_report_source import item_report_source
from Src.Logics.unit_report_source import unit_report_source
from Src.Logics.recipe_report_source import recipe_report_source
from Src.Models.item_model import item_model
from Src.Models.recipe_model import recipe_model
from Src.Models.unit_model import unit_model


class report_source_factory(abstract_report_source_factory):
    """Создаёт обработчики номенклатуры, единиц и рецептов."""

    def __init__(self) -> None:
        """Регистрирует обработчики поддерживаемых типов."""
        self.__mapping = {
            item_model: item_report_source,
            unit_model: unit_report_source,
            recipe_model: recipe_report_source,
        }

    def create(self, entity_type: type[entity_model]) -> abstract_report_source[Any]:
        """Проверяет тип сущности и создаёт соответствующий обработчик."""
        if not isinstance(entity_type, type) or entity_type not in self.__mapping:
            raise arguments_exception("entity_type", "Для этого типа отчёты не поддерживаются")
        return self.__mapping[entity_type]()
