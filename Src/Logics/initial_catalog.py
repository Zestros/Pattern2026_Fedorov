from datetime import datetime

from Src.Core.entity_model import entity_model
from Src.Logics.collect_entity_graph import collect_entity_graph
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.transaction_model import transaction_model
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


def demo_transactions(catalog: tuple[entity_model, ...]) -> tuple[transaction_model, ...]:
    """Создаёт фиксированные движения, на которых можно проверить складскую ОСВ."""
    warehouse = next(model for model in catalog if isinstance(model, warehouse_model))
    items = {model.name: model for model in catalog if isinstance(model, item_model)}
    flour = items["Мука"]
    water = items["Вода"]
    return (
        transaction_model(datetime(2026, 1, 31), warehouse, flour, flour.unit.base_unit, 10),
        transaction_model(datetime(2026, 2, 1), warehouse, flour, flour.unit.base_unit, 5),
        transaction_model(datetime(2026, 2, 28), warehouse, flour, flour.unit.base_unit, -3),
        transaction_model(datetime(2026, 3, 1), warehouse, flour, flour.unit.base_unit, 20),
        transaction_model(datetime(2026, 2, 10), warehouse, water, water.unit.base_unit, 7),
    )
