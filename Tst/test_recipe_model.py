"""Юнит-тесты технологической карты."""

import pytest

from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.unit_model import unit_model
from Src.Models.recipe_model import recipe_model
from Src.Models.recipe_ingredient_model import recipe_ingredient_model


def test_calculated_weights_recipe_model_ingredients():
    """
    <summary>
    Карта содержит 0.3 кг муки и 200 г сахара.
    Брутто составляет 500 г, нетто при коэффициенте 0.8 — 400 г.
    </summary>
    """
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    group = group_model("Бакалея")
    flour = item_model("Мука", "Мука пшеничная", group, kilogram)
    sugar = item_model("Сахар", "Сахар белый", group, gram)

    recipe = recipe_model("Смесь", gram, 0.8)
    recipe.add_ingredient(recipe_ingredient_model(flour, 0.3))
    recipe.add_ingredient(recipe_ingredient_model(sugar, 200))

    assert recipe.gross_weight == pytest.approx(500)
    assert recipe.net_weight == pytest.approx(400)


def test_updated_weights_add_ingredient_new_product():
    """
    <summary>
    Пустая карта имеет нулевые массы.
    Добавление 100 г продукта сразу меняет брутто и нетто.
    </summary>
    """
    gram = unit_model("грамм")
    flour = item_model(
        "Мука", "Мука пшеничная", group_model("Бакалея"), gram,
    )
    recipe = recipe_model("Смесь", gram, 0.9)

    assert recipe.gross_weight == 0
    assert recipe.net_weight == 0

    recipe.add_ingredient(recipe_ingredient_model(flour, 100))

    assert recipe.gross_weight == pytest.approx(100)
    assert recipe.net_weight == pytest.approx(90)


def test_updated_weights_remove_ingredient_existing_product():
    """
    <summary>
    Удаление сахара оставляет только массу муки.
    Удаление последнего ингредиента обнуляет обе массы.
    </summary>
    """
    gram = unit_model("грамм")
    group = group_model("Бакалея")
    flour = item_model("Мука", "Мука пшеничная", group, gram)
    sugar = item_model("Сахар", "Сахар белый", group, gram)
    flour_row = recipe_ingredient_model(flour, 300)
    sugar_row = recipe_ingredient_model(sugar, 100)
    recipe = recipe_model("Смесь", gram, 0.8)
    recipe.add_ingredient(flour_row)
    recipe.add_ingredient(sugar_row)

    recipe.remove_ingredient(sugar_row)

    assert recipe.ingredients == (flour_row,)
    assert recipe.gross_weight == pytest.approx(300)
    assert recipe.net_weight == pytest.approx(240)

    recipe.remove_ingredient(flour_row)

    assert recipe.gross_weight == 0
    assert recipe.net_weight == 0


def test_updated_weights_recipe_model_changed_quantity():
    """
    <summary>
    Изменение количества в строке автоматически меняет массы карты.
    Коэффициент больше единицы допускает увеличение массы.
    </summary>
    """
    gram = unit_model("грамм")
    product = item_model(
        "Крупа", "Крупа для варки", group_model("Бакалея"), gram,
    )
    ingredient = recipe_ingredient_model(product, 100)
    recipe = recipe_model("Варёная крупа", gram, 2)
    recipe.add_ingredient(ingredient)

    assert recipe.net_weight == pytest.approx(200)

    ingredient.quantity = 150

    assert recipe.gross_weight == pytest.approx(150)
    assert recipe.net_weight == pytest.approx(300)