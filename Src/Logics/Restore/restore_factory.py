from types import SimpleNamespace

from Src.Core.abstract_model import abstract_model
from Src.Core.abstract_restore_handler import abstract_restore_handler
from Src.Core.entity_model import entity_model
from Src.Core.entity_type_enum import entity_type_enum
from Src.Core.exception import arguments_exception
from Src.Core.report_type_enum import report_type_enum
from Src.Logics.Restore.collection_restore import dict_restore, list_restore, tuple_restore
from Src.Logics.Restore.model_restore import (
    model_restore, recipe_restore, settings_restore, storage_restore, unit_restore,
)
from Src.Logics.Restore.value_restore import datetime_restore, enum_restore
from Src.Models.company_model import company_model
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.ratio_unit_model import ratio_unit_model
from Src.Models.ratio_value_model import ratio_value_model
from Src.Models.recipe_ingredient_model import recipe_ingredient_model
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.warehouse_model import warehouse_model


class restore_factory:
    """Выбирает явно зарегистрированный обработчик по $type без восстановления данных."""

    def __init__(self) -> None:
        """Регистрирует обработчики формата, конструкторы моделей и особые правила."""
        handlers = [
            list_restore(), tuple_restore(), dict_restore(), datetime_restore(),
            enum_restore(report_type_enum), enum_restore(entity_type_enum),
            model_restore(abstract_model, []), model_restore(entity_model, []),
            model_restore(SimpleNamespace, []),
            model_restore(group_model, ["name"]),
            model_restore(warehouse_model, ["name"]),
            model_restore(ratio_unit_model, ["numerator_unit", "denominator_unit"]),
            model_restore(ratio_value_model, ["value", "unit"]),
            model_restore(item_model, ["name", "full_name", "group", "unit", "mass_ratio"]),
            model_restore(recipe_item_model, ["name", "full_name", "group", "unit", "recipe", "output_quantity"]),
            model_restore(recipe_ingredient_model, ["item", "quantity", "is_packaging"]),
            model_restore(company_model, ["name", "inn", "bik", "account", "ownership_form"]),
            unit_restore(), recipe_restore(), settings_restore(), storage_restore(),
        ]
        self.__handlers = {handler.type_name: handler for handler in handlers}

    def create(self, node: dict) -> abstract_restore_handler:
        """Возвращает обработчик известного типа и отклоняет неизвестное имя."""
        type_name = node.get("$type")
        if not isinstance(type_name, str):
            raise arguments_exception("$type", "Не указан тип значения")
        if type_name not in self.__handlers:
            raise arguments_exception("$type", f"Неизвестный тип: {type_name}")
        return self.__handlers[type_name]
