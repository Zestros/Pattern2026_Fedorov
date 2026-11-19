from Src.Dtos.group_dto import group_dto
from Src.Dtos.warehouse_dto import warehouse_dto
from Src.Dtos.unit_dto import unit_dto
from Src.Dtos.item_dto import item_dto, recipe_item_dto, mass_ratio_dto, ratio_unit_dto
from Src.Dtos.recipe_dto import recipe_dto, ingredient_dto
from Src.Models.group_model import group_model
from Src.Models.warehouse_model import warehouse_model
from Src.Models.unit_model import unit_model
from Src.Models.item_model import item_model
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.recipe_model import recipe_model
from Src.Models.recipe_ingredient_model import recipe_ingredient_model
from Src.Models.ratio_value_model import ratio_value_model
from Src.Models.ratio_unit_model import ratio_unit_model
from Src.Logics.dto_mapping import mapping_registry, model_mapping
from Src.Logics.resource_catalog import resource_catalog, resource_definition


def entity_mappings() -> mapping_registry:
    """Создаёт реестр соответствий DTO и доменных типов."""
    return mapping_registry((
        model_mapping(group_dto, group_model),
        model_mapping(warehouse_dto, warehouse_model),
        model_mapping(unit_dto, unit_model),
        model_mapping(item_dto, item_model),
        model_mapping(recipe_item_dto, recipe_item_model),
        model_mapping(recipe_dto, recipe_model),
        model_mapping(ingredient_dto, recipe_ingredient_model),
        model_mapping(mass_ratio_dto, ratio_value_model),
        model_mapping(ratio_unit_dto, ratio_unit_model),
    ))


def entity_resources(mappings: mapping_registry) -> resource_catalog:
    """Регистрирует внешние имена API независимо от алгоритмов преобразования."""
    return resource_catalog(mappings, (
        resource_definition("group", group_dto),
        resource_definition("warehouse", warehouse_dto, searchable=False),
        resource_definition("unit", unit_dto),
        resource_definition("item", item_dto, {"recipe": recipe_item_dto}),
        resource_definition("recipe", recipe_dto),
    ))
