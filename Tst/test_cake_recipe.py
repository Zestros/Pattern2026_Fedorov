"""Юнит-тесты составного торта из коржей и крема."""

import pytest

from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.unit_model import unit_model


def test_created_cake_create_cake_nested_recipes():
    """<summary>Фабрика создаёт торт из трёх коржей и одной порции крема с отдельными картами.</summary>"""
    gram = unit_model("грамм")
    piece = unit_model.create_piece()
    group = group_model.create_grocery()
    cake = recipe_item_model.create_cake(group, gram, piece)

    assert cake.name == "Бисквитный торт"
    assert cake.output_quantity == 1
    assert len(cake.recipe.ingredients) == 2
    layers, cream = cake.recipe.ingredients
    assert isinstance(layers.item, recipe_item_model)
    assert isinstance(cream.item, recipe_item_model)
    assert layers.quantity == 3
    assert cream.quantity == 1
    assert layers.item.output_quantity == 4
    assert cream.item.output_quantity == 1
    assert len(layers.recipe.ingredients) == 3
    assert len(cream.recipe.ingredients) == 2
    assert layers.recipe.ingredients[1].item is cream.recipe.ingredients[1].item
    assert all(row.recipe is None for row in layers.recipe.ingredients)
    assert all(row.recipe is None for row in cream.recipe.ingredients)


def test_calculated_weights_create_cake_partial_layer_batch():
    """<summary>Три из четырёх коржей дают 405 г, крем 400 г, весь торт 805 г.</summary>"""
    gram = unit_model("грамм")
    cake = recipe_item_model.create_cake(group_model.create_grocery(), gram, unit_model.create_piece())
    layers, cream = cake.recipe.ingredients

    assert layers.recipe.gross_weight == pytest.approx(600)
    assert layers.recipe.net_weight == pytest.approx(540)
    assert layers.item.calculate_mass(1, gram) == pytest.approx(135)
    assert cream.recipe.gross_weight == pytest.approx(400)
    assert cream.recipe.net_weight == pytest.approx(400)
    assert cake.recipe.gross_weight == pytest.approx(805)
    assert cake.recipe.net_weight == pytest.approx(805)
    assert cake.calculate_mass(1, gram) == pytest.approx(805)
    assert cake.calculate_mass(0.5, gram) == pytest.approx(402.5)


def test_updated_weights_create_cake_changed_layer_recipe():
    """<summary>При увеличении муки на 100 г масса торта автоматически увеличивается на 67.5 г.</summary>"""
    gram = unit_model("грамм")
    cake = recipe_item_model.create_cake(group_model.create_grocery(), gram, unit_model.create_piece())
    layers = cake.recipe.ingredients[0]
    flour = layers.recipe.ingredients[0]
    flour.quantity = 300

    assert layers.recipe.net_weight == pytest.approx(630)
    assert cake.recipe.gross_weight == pytest.approx(872.5)
    assert cake.recipe.net_weight == pytest.approx(872.5)


def test_updated_weights_create_cake_added_removed_cream_ingredient():
    """<summary>Добавление 20 г какао во вложенный крем меняет торт до 825 г; удаление возвращает 805 г.</summary>"""
    gram = unit_model("грамм")
    group = group_model.create_grocery()
    cake = recipe_item_model.create_cake(group, gram, unit_model.create_piece())
    cream = cake.recipe.ingredients[1].recipe
    cocoa = item_model("Какао", "Какао-порошок", group, gram)
    row = cream.add_ingredient(cocoa, 20)

    assert cake.recipe.gross_weight == pytest.approx(825)
    assert cake.recipe.net_weight == pytest.approx(825)
    cream.remove_ingredient(row)
    assert cake.recipe.gross_weight == pytest.approx(805)
    assert cake.recipe.net_weight == pytest.approx(805)


def test_updated_weights_create_cake_changed_assembly():
    """<summary>Торт из двух коржей весит 670 г, после удаления крема остаётся 270 г.</summary>"""
    gram = unit_model("грамм")
    cake = recipe_item_model.create_cake(group_model.create_grocery(), gram, unit_model.create_piece())
    layers, cream = cake.recipe.ingredients
    layers.quantity = 2
    assert cake.recipe.gross_weight == pytest.approx(670)
    assert cake.recipe.net_weight == pytest.approx(670)
    cake.recipe.remove_ingredient(cream)
    assert cake.recipe.gross_weight == pytest.approx(270)
    assert cake.recipe.net_weight == pytest.approx(270)
