"""Юнит-тесты текстового репорта."""

from Src.Logics.text_report import text_report
from Src.Models.group_model import group_model
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.unit_model import unit_model



def test_created_text_build_recipe_with_two_ingredients():
    """
    <summary>
    Отчёт содержит заголовок и обе строки состава торта:
    три коржа массой 405 г и порцию крема массой 400 г.
    </summary>
    """
    # Подготовка
    cake = recipe_item_model.create_cake(
        group_model.create_grocery(),
        unit_model("грамм"),
        unit_model.create_piece(),
    )
    layers, cream = cake.recipe.ingredients

    # Действие
    result = text_report().build(cake.recipe)

    # Проверка
    assert result.text.splitlines() == [
        "Код | Наименование | Брутто | Нетто",
        f"{layers.unique_code} | Бисквитный корж | 405.0 | 405.0",
        f"{cream.unique_code} | Порция крема | 400.0 | 400.0",
    ]