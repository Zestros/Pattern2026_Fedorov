"""Юнит-тесты вложенных карт, упаковки и защиты состава."""

import pytest

from Src.Core.exception import arguments_exception
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.recipe_model import recipe_model
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.unit_model import unit_model


def test_updated_weights_add_ingredient_convenient_creation():
    """<summary>Карта создаёт строку; её количество меняет обе массы, удаление обнуляет их.</summary>"""
    gram = unit_model("грамм")
    flour = item_model("Мука", "Мука", group_model("Продукты"), gram)
    recipe = recipe_model("Тесто", gram, 0.8)
    row = recipe.add_ingredient(flour, 100)
    assert row.item is flour
    assert row.recipe is None
    row.quantity = 200
    assert recipe.gross_weight == pytest.approx(200)
    assert recipe.net_weight == pytest.approx(160)
    recipe.remove_ingredient(row)
    assert recipe.gross_weight == 0
    assert recipe.net_weight == 0


def test_calculated_weights_recipe_model_packaging():
    """<summary>Упаковка входит только в брутто и не умножается на коэффициент обработки.</summary>"""
    gram = unit_model("грамм")
    group = group_model("Продукты")
    food = item_model("Продукт", "Продукт", group, gram)
    packaging = item_model("Бумага", "Бумага", group, gram)
    recipe = recipe_model("Упакованный продукт", gram, 0.8)
    recipe.add_ingredient(food, 100)
    row = recipe.add_ingredient(packaging, 15, is_packaging=True)
    assert row.is_packaging is True
    assert recipe.packaging_weight == pytest.approx(15)
    assert recipe.gross_weight == pytest.approx(115)
    assert recipe.net_weight == pytest.approx(80)
    recipe.remove_ingredient(row)
    assert recipe.gross_weight == pytest.approx(100)


def test_updated_weights_recipe_item_model_nested_recipe():
    """<summary>Два из шести изделий берут треть нетто карты; изменение сырья обновляет родителя.</summary>"""
    gram = unit_model("грамм")
    piece = unit_model("штука")
    group = group_model("Продукты")
    flour = item_model("Мука", "Мука", group, gram)
    inner = recipe_model("Лепёшки", gram, 0.9)
    flour_row = inner.add_ingredient(flour, 500)
    bread = recipe_item_model("Лепёшка", "Лепёшка", group, piece, inner, output_quantity=6)
    outer = recipe_model("Порция", gram, 0.8)
    row = outer.add_ingredient(bread, 2)
    assert row.recipe is inner
    assert outer.gross_weight == pytest.approx(150)
    assert outer.net_weight == pytest.approx(120)
    flour_row.quantity = 600
    assert outer.gross_weight == pytest.approx(180)
    assert outer.net_weight == pytest.approx(144)


def test_calculated_weights_recipe_model_nested_packaging():
    """<summary>Упаковка вложенного продукта не становится едой и не подвергается обработке повторно.</summary>"""
    gram = unit_model("грамм")
    piece = unit_model("штука")
    group = group_model("Продукты")
    food = item_model("Продукт", "Продукт", group, gram)
    paper = item_model("Бумага", "Бумага", group, gram)
    inner = recipe_model("Упакованная порция", gram, 0.8)
    inner.add_ingredient(food, 100)
    inner.add_ingredient(paper, 10, is_packaging=True)
    portion = recipe_item_model("Порция", "Порция", group, piece, inner, output_quantity=1)
    outer = recipe_model("Набор", gram, 0.5)
    outer.add_ingredient(portion, 2)
    assert outer.gross_weight == pytest.approx(180)
    assert outer.net_weight == pytest.approx(80)
    assert outer.packaging_weight == pytest.approx(20)


def test_calculated_mass_recipe_item_model_weight_quantity():
    """<summary>Количество весового полуфабриката задаёт готовую массу без выхода в штуках.</summary>"""
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    group = group_model("Продукты")
    inner = recipe_model("Тесто", gram)
    dough = recipe_item_model("Тесто", "Тесто", group, kilogram, inner)
    assert dough.calculate_mass(0.2, gram) == pytest.approx(200)
    assert dough.calculate_mass(200, kilogram, gram) == pytest.approx(0.2)


def test_arguments_exception_add_ingredient_direct_cycle():
    """<summary>Карта не может содержать собственный продукт; состав при ошибке не меняется.</summary>"""
    gram = unit_model("грамм")
    recipe = recipe_model("Тесто", gram)
    dough = recipe_item_model("Тесто", "Тесто", group_model("Продукты"), gram, recipe)
    with pytest.raises(arguments_exception):
        recipe.add_ingredient(dough, 1)
    assert recipe.ingredients == ()


def test_arguments_exception_add_ingredient_indirect_cycle():
    """<summary>Добавление последней связи в цепочке А → Б → В → А запрещается.</summary>"""
    gram = unit_model("грамм")
    group = group_model("Продукты")
    first = recipe_model("А", gram)
    second = recipe_model("Б", gram)
    third = recipe_model("В", gram)
    a = recipe_item_model("А", "А", group, gram, first)
    b = recipe_item_model("Б", "Б", group, gram, second)
    c = recipe_item_model("В", "В", group, gram, third)
    first.add_ingredient(b, 1)
    second.add_ingredient(c, 1)
    with pytest.raises(arguments_exception):
        third.add_ingredient(a, 1)
    assert third.ingredients == ()


def test_calculated_mass_recipe_model_shared_subrecipe():
    """<summary>Общий полуфабрикат в двух ветках разрешён и учитывается в обеих.</summary>"""
    gram = unit_model("грамм")
    piece = unit_model("штука")
    group = group_model("Продукты")
    base = recipe_model("Основа", gram)
    base.add_ingredient(item_model("Мука", "Мука", group, gram), 100)
    base_item = recipe_item_model("Основа", "Основа", group, piece, base, 1)
    left = recipe_model("Левая", gram)
    right = recipe_model("Правая", gram)
    left.add_ingredient(base_item, 1)
    right.add_ingredient(base_item, 2)
    root = recipe_model("Набор", gram)
    root.add_ingredient(recipe_item_model("Левая", "Левая", group, piece, left, 1), 1)
    root.add_ingredient(recipe_item_model("Правая", "Правая", group, piece, right, 1), 1)
    assert root.net_weight == pytest.approx(300)


def test_arguments_exception_add_ingredient_duplicate_row():
    """<summary>Повторное добавление одной строки запрещено, отдельные строки того же продукта разрешены.</summary>"""
    gram = unit_model("грамм")
    flour = item_model("Мука", "Мука", group_model("Продукты"), gram)
    recipe = recipe_model("Тесто", gram)
    row = recipe.add_ingredient(flour, 100)
    with pytest.raises(arguments_exception):
        recipe.add_ingredient(row)
    recipe.add_ingredient(flour, 50)
    assert recipe.net_weight == pytest.approx(150)


def test_arguments_exception_recipe_item_model_missing_output():
    """<summary>Штучному продукту нужен положительный выход карты в его единице учёта.</summary>"""
    gram = unit_model("грамм")
    piece = unit_model("штука")
    recipe = recipe_model("Лепёшки", gram)
    with pytest.raises(arguments_exception):
        recipe_item_model("Лепёшка", "Лепёшка", group_model("Продукты"), piece, recipe)


def test_read_only_references_recipe_model_cycle_protection():
    """<summary>Публичная замена ссылок на продукт и карту запрещена, обход проверки циклов невозможен.</summary>"""
    gram = unit_model("грамм")
    inner = recipe_model("Основа", gram)
    product = recipe_item_model("Основа", "Основа", group_model("Продукты"), gram, inner)
    outer = recipe_model("Блюдо", gram)
    row = outer.add_ingredient(product, 1)
    with pytest.raises(AttributeError):
        product.recipe = outer
    with pytest.raises(AttributeError):
        row.item = product


def test_calculated_packaging_recipe_item_model_weight_fraction():
    """<summary>200 г из партии с нетто 400 г получают половину её упаковки.</summary>"""
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    group = group_model("Продукты")
    inner = recipe_model("Упакованный продукт", gram, 0.8)
    inner.add_ingredient(item_model("Продукт", "Продукт", group, gram), 500)
    inner.add_ingredient(item_model("Бумага", "Бумага", group, gram), 20, is_packaging=True)
    product = recipe_item_model("Продукт", "Продукт", group, kilogram, inner)
    outer = recipe_model("Порция", gram)
    outer.add_ingredient(product, 0.2)
    assert outer.net_weight == pytest.approx(200)
    assert outer.packaging_weight == pytest.approx(10)
    assert outer.gross_weight == pytest.approx(210)


def test_updated_mass_recipe_item_model_removed_inner_ingredient():
    """<summary>Удаление последнего сырья обнуляет массу штучного продукта в родительской карте.</summary>"""
    gram = unit_model("грамм")
    piece = unit_model("штука")
    group = group_model("Продукты")
    inner = recipe_model("Лепёшка", gram)
    row = inner.add_ingredient(item_model("Мука", "Мука", group, gram), 100)
    product = recipe_item_model("Лепёшка", "Лепёшка", group, piece, inner, 1)
    outer = recipe_model("Порция", gram)
    outer.add_ingredient(product, 2)
    assert outer.net_weight == pytest.approx(200)
    inner.remove_ingredient(row)
    assert outer.net_weight == 0
    assert outer.gross_weight == 0


def test_arguments_exception_recipe_item_model_zero_output():
    """<summary>Нулевой выход партии отклоняется, предотвращая деление на ноль.</summary>"""
    gram = unit_model("грамм")
    recipe = recipe_model("Лепёшки", gram)
    with pytest.raises(arguments_exception):
        recipe_item_model("Лепёшка", "Лепёшка", group_model("Продукты"), unit_model("штука"), recipe, 0)


def test_preserved_quantity_recipe_ingredient_model_invalid_change():
    """<summary>Отрицательное количество отклоняется без изменения строки и массы карты.</summary>"""
    gram = unit_model("грамм")
    recipe = recipe_model("Смесь", gram)
    row = recipe.add_ingredient(item_model("Мука", "Мука", group_model("Продукты"), gram), 100)
    with pytest.raises(arguments_exception):
        row.quantity = -1
    assert row.quantity == 100
    assert recipe.net_weight == pytest.approx(100)


def test_updated_weights_recipe_model_added_nested_ingredient():
    """<summary>Новый ингредиент вложенной карты изменяет брутто и нетто родителя.</summary>"""
    gram = unit_model("грамм")
    piece = unit_model("штука")
    group = group_model("Бакалея")
    flour = item_model("Мука", "Мука пшеничная", group, gram)
    salt = item_model("Соль", "Соль пищевая", group, gram)
    inner = recipe_model("Заготовка", gram, 0.9)
    inner.add_ingredient(flour, 100)
    product = recipe_item_model("Заготовка", "Заготовка", group, piece, inner, 1)
    outer = recipe_model("Блюдо", gram, 0.8)
    outer.add_ingredient(product, 2)
    assert outer.gross_weight == pytest.approx(180)
    assert outer.net_weight == pytest.approx(144)
    inner.add_ingredient(salt, 10)
    assert outer.gross_weight == pytest.approx(198)
    assert outer.net_weight == pytest.approx(158.4)
