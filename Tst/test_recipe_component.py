"""Юнит-тесты общего поведения компонентов и строк рецепта."""

import pytest

from Src.Core.exception import arguments_exception
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.recipe_model import recipe_model
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.recipe_ingredient_model import recipe_ingredient_model
from Src.Models.unit_model import unit_model


def test_arguments_exception_recipe_item_model_none_recipe():
    """
    <summary>
    None вместо карты запрещён при создании составного продукта.
    Ошибка содержит название обязательного поля recipe.
    </summary>
    """
    # Подготовка
    group = group_model("Продукты")
    gram = unit_model("грамм")

    # Действие
    with pytest.raises(arguments_exception) as error:
        recipe_item_model("Продукт", "Продукт", group, gram, None)

    # Проверка
    assert "Поле: recipe" in str(error.value)


def test_calculated_weights_recipe_ingredient_model_composite_product():
    """
    <summary>
    Вложенная порция содержит 100 г еды и 10 г упаковки.
    Для двух порций строка возвращает нетто 200 г и брутто 220 г.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    piece = unit_model("штука")
    group = group_model("Продукты")
    inner = recipe_model("Порция", gram)
    inner.add_ingredient(item_model("Еда", "Еда", group, gram), 100)
    inner.add_ingredient(item_model("Бумага", "Бумага", group, gram), 10, is_packaging=True)
    product = recipe_item_model("Порция", "Порция", group, piece, inner, 1)
    row = recipe_ingredient_model(product, 2)

    # Действие
    net = row.calculate_net_weight(gram)
    gross = row.calculate_gross_weight(gram)

    # Проверка
    assert net == pytest.approx(200)
    assert gross == pytest.approx(220)


def test_zero_net_weight_recipe_ingredient_model_packaging():
    """
    <summary>
    Упаковочная строка не вносит пищевую массу.
    Полная масса строки составляет 15 г.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    paper = item_model("Бумага", "Бумага", group_model("Упаковка"), gram)
    row = recipe_ingredient_model(paper, 15, is_packaging=True)

    # Действие
    net = row.calculate_net_weight(gram)
    gross = row.calculate_gross_weight(gram)

    # Проверка
    assert net == 0
    assert gross == pytest.approx(15)


def test_equal_weights_item_model_plain_product():
    """
    <summary>
    Обычный продукт без упаковки предоставляет одинаковые брутто и нетто.
    Количество 0.3 кг переводится в 300 г обоими методами.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    flour = item_model("Мука", "Мука", group_model("Бакалея"), kilogram)

    # Действие
    net = flour.calculate_net_weight(0.3, gram)
    gross = flour.calculate_gross_weight(0.3, gram)

    # Проверка
    assert net == pytest.approx(300)
    assert gross == pytest.approx(300)


def test_calculated_weights_recipe_model_custom_component():
    """
    <summary>
    Карта принимает реализацию общего контракта без наследования item_model.
    Собственные нетто 100 г и брутто 110 г компонента учитываются для двух единиц.
    </summary>
    """
    # Подготовка
    from Src.Core.abstract_recipe_component import abstract_recipe_component

    class custom_component(abstract_recipe_component):
        """Компонент с независимыми нормами двух масс для проверки контракта."""

        def calculate_net_weight(self, quantity, target_unit):
            """Возвращает чистую массу указанного количества."""
            return quantity * 100

        def calculate_gross_weight(self, quantity, target_unit):
            """Возвращает массу с упаковкой указанного количества."""
            return quantity * 110

        def validate_recipe_path(self, path):
            """Завершает обход компонента без вложенных карт."""
            return

    recipe = recipe_model("Проверка контракта", unit_model("грамм"))

    # Действие
    recipe.add_ingredient(custom_component(), 2)
    net = recipe.net_weight
    gross = recipe.gross_weight
    packaging = recipe.packaging_weight

    # Проверка
    assert net == pytest.approx(200)
    assert gross == pytest.approx(220)
    assert packaging == pytest.approx(20)
