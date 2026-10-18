"""Юнит-тесты текстового репорта."""

from Src.Logics.text_report import text_report
from Src.Logics.recipe_report_source import recipe_report_source
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
    result = text_report().build(recipe_report_source().build(cake.recipe))

    # Проверка
    assert result.content.splitlines() == [
        cake.recipe.name,
        f"Код: {cake.recipe.unique_code}",
        f"Наименование: {cake.recipe.name}",
        f"Код единицы массы: {cake.recipe.mass_unit.unique_code}",
        f"Единица массы: {cake.recipe.mass_unit.name}",
        "Брутто: 805.0",
        "Нетто: 805.0",
        "Код строки | Наименование | Код номенклатуры | Количество | Брутто | Нетто",
        f"{layers.unique_code} | Бисквитный корж | {layers.item.unique_code} | {layers.quantity} | 405.0 | 405.0",
        f"{cream.unique_code} | Порция крема | {cream.item.unique_code} | {cream.quantity} | 400.0 | 400.0",
    ]