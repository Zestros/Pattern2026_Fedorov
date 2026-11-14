from Src.Core.entity_model import entity_model
from Src.Logics.collect_entity_graph import collect_entity_graph
from Src.Models.group_model import group_model
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.unit_model import unit_model
from Src.Models.warehouse_model import warehouse_model


def initial_catalog() -> tuple[entity_model, ...]:
    """Создаёт стартовые сущности и собирает их полные связи для регистрации."""
    group = group_model.create_grocery()
    kilogram = unit_model.create_kilogram()
    gram = kilogram.base_unit
    liter = unit_model.create_liter()
    piece = unit_model.create_piece()
    dough = recipe_item_model.create_dough(group, kilogram, liter)
    bread = recipe_item_model.create_flatbreads(dough, piece)
    cake = recipe_item_model.create_cake(group, gram, piece)
    return collect_entity_graph((
        group, warehouse_model.create_main(), gram, kilogram, liter.base_unit, liter, piece,
        *(row.item for row in dough.recipe.ingredients), dough, bread, cake,
    ))
