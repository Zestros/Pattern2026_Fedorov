from Src.Core.abstract_model import abstract_model
from Src.Core.entity_model import entity_model
from Src.Core.entity_type_enum import entity_type_enum
from Src.Core.report_type_enum import report_type_enum
from Src.Logics.Restore.datetime_restore import datetime_restore
from Src.Logics.Restore.dict_restore import dict_restore
from Src.Logics.Restore.enum_restore import enum_restore
from Src.Logics.Restore.list_restore import list_restore
from Src.Logics.Restore.recipe_restore import recipe_restore
from Src.Logics.Restore.storage_restore import storage_restore
from Src.Logics.Restore.tuple_restore import tuple_restore
from Src.Models.company_model import company_model
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.ratio_unit_model import ratio_unit_model
from Src.Models.ratio_value_model import ratio_value_model
from Src.Models.recipe_ingredient_model import recipe_ingredient_model
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.recipe_model import recipe_model
from Src.Models.settings_model import settings_model
from Src.Models.unit_model import unit_model
from Src.Models.warehouse_model import warehouse_model


def register_restore_handlers(factory) -> None:
    """Регистрирует типы при создании фабрики независимо от стартовых данных."""
    model_types = (
        abstract_model, entity_model, group_model, warehouse_model,
        ratio_unit_model, ratio_value_model, item_model, recipe_item_model,
        recipe_ingredient_model, company_model, settings_model, unit_model, recipe_model,
    )
    for model_type in model_types:
        factory.add_model(model_type)

    for handler in (
        list_restore(), tuple_restore(), dict_restore(), datetime_restore(),
        enum_restore(report_type_enum), enum_restore(entity_type_enum),
        recipe_restore(), storage_restore(),
    ):
        factory.add_handler(handler)
