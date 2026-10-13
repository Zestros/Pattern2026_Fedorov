"""Интеграционные тесты сборки торта и пересчёта вложенных карт."""

import pytest

from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.unit_model import unit_model


def test_created_cake_create_cake_nested_recipes():
    """
    <summary>
    Фабрика создаёт торт из трёх коржей и одной порции крема с отдельными картами.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    piece = unit_model.create_piece()
    group = group_model.create_grocery()

    # Действие
    cake = recipe_item_model.create_cake(group, gram, piece)
    layers, cream = cake.recipe.ingredients

    # Проверка
    assert cake.name == "Бисквитный торт"
    assert cake.output_quantity == 1
    assert len(cake.recipe.ingredients) == 2

    assert isinstance(layers.item, recipe_item_model)
    assert isinstance(cream.item, recipe_item_model)
    assert layers.quantity == 3
    assert cream.quantity == 1
    assert layers.item.output_quantity == 4
    assert cream.item.output_quantity == 1
    assert len(layers.item.recipe.ingredients) == 3
    assert len(cream.item.recipe.ingredients) == 2
    assert layers.item.recipe.ingredients[1].item is cream.item.recipe.ingredients[1].item
    assert all(not isinstance(row.item, recipe_item_model) for row in layers.item.recipe.ingredients)
    assert all(not isinstance(row.item, recipe_item_model) for row in cream.item.recipe.ingredients)


def test_calculated_weights_calculate_mass_partial_layer_batch():
    """
    <summary>
    Три из четырёх коржей дают 405 г, крем — 400 г.
    Проверяются массы вложенных партий, целого торта и половины торта.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    cake = recipe_item_model.create_cake(group_model.create_grocery(), gram, unit_model.create_piece())
    layers, cream = cake.recipe.ingredients

    # Действие
    layers_gross = layers.item.recipe.gross_weight
    layers_net = layers.item.recipe.net_weight
    layer_mass = layers.item.calculate_mass(1, gram)
    cream_gross = cream.item.recipe.gross_weight
    cream_net = cream.item.recipe.net_weight
    cake_gross = cake.recipe.gross_weight
    cake_net = cake.recipe.net_weight
    whole_mass = cake.calculate_mass(1, gram)
    half_mass = cake.calculate_mass(0.5, gram)

    # Проверка
    assert layers_gross == pytest.approx(600)
    assert layers_net == pytest.approx(540)
    assert layer_mass == pytest.approx(135)
    assert cream_gross == pytest.approx(400)
    assert cream_net == pytest.approx(400)
    assert cake_gross == pytest.approx(805)
    assert cake_net == pytest.approx(805)
    assert whole_mass == pytest.approx(805)
    assert half_mass == pytest.approx(402.5)


def test_updated_weights_quantity_changed_layer_recipe():
    """
    <summary>
    При увеличении муки на 100 г масса торта автоматически увеличивается на 67.5 г.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    cake = recipe_item_model.create_cake(group_model.create_grocery(), gram, unit_model.create_piece())
    layers = cake.recipe.ingredients[0]
    flour = layers.item.recipe.ingredients[0]

    # Действие
    flour.quantity = 300

    # Проверка
    assert layers.item.recipe.net_weight == pytest.approx(630)
    assert cake.recipe.gross_weight == pytest.approx(872.5)
    assert cake.recipe.net_weight == pytest.approx(872.5)


def test_updated_weights_add_ingredient_nested_cream():
    """
    <summary>
    Добавление 20 г какао во вложенный крем увеличивает обе массы торта до 825 г.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    group = group_model.create_grocery()
    cake = recipe_item_model.create_cake(group, gram, unit_model.create_piece())
    cream = cake.recipe.ingredients[1].item.recipe
    cocoa = item_model("Какао", "Какао-порошок", group, gram)

    # Действие
    cream.add_ingredient(cocoa, 20)

    # Проверка
    assert cake.recipe.gross_weight == pytest.approx(825)
    assert cake.recipe.net_weight == pytest.approx(825)



def test_updated_weights_quantity_changed_assembly():
    """
    <summary>
    Уменьшение количества коржей до двух даёт брутто и нетто торта 670 г.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    cake = recipe_item_model.create_cake(group_model.create_grocery(), gram, unit_model.create_piece())
    layers, cream = cake.recipe.ingredients

    # Действие
    layers.quantity = 2

    # Проверка
    assert cake.recipe.gross_weight == pytest.approx(670)
    assert cake.recipe.net_weight == pytest.approx(670)



def test_restored_weights_remove_ingredient_nested_cream():
    """
    <summary>
    Из крема удаляется предварительно добавленная строка какао.
    Брутто и нетто родительского торта возвращаются к исходным 805 г.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    group = group_model.create_grocery()
    cake = recipe_item_model.create_cake(group, gram, unit_model.create_piece())
    cream = cake.recipe.ingredients[1].item.recipe
    cocoa = item_model("Какао", "Какао-порошок", group, gram)
    row = cream.add_ingredient(cocoa, 20)

    # Действие
    cream.remove_ingredient(row)

    # Проверка
    assert cake.recipe.gross_weight == pytest.approx(805)
    assert cake.recipe.net_weight == pytest.approx(805)


def test_reduced_weights_remove_ingredient_cream_from_cake():
    """
    <summary>
    Из торта с двумя коржами удаляется строка крема.
    Оставшиеся коржи дают брутто и нетто 270 г.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    cake = recipe_item_model.create_cake(group_model.create_grocery(), gram, unit_model.create_piece())
    layers, cream = cake.recipe.ingredients
    layers.quantity = 2

    # Действие
    cake.recipe.remove_ingredient(cream)

    # Проверка
    assert cake.recipe.gross_weight == pytest.approx(270)
    assert cake.recipe.net_weight == pytest.approx(270)
