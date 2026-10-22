"""Модульные тесты выбора конверторов, структуры результата и циклов."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from Src.Core.abstract_convertor import abstract_convertor
from Src.Core.abstract_model import abstract_model
from Src.Dtos.conversion_context_dto import conversion_context_dto
from Src.Core.exception import arguments_exception
from Src.Logics.basic_convertor import basic_convertor
from Src.Logics.convert_factory import convert_factory
from Src.Logics.datetime_convertor import datetime_convertor
from Src.Logics.reference_convertor import reference_convertor
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.recipe_model import recipe_model
from Src.Models.unit_model import unit_model


@pytest.mark.parametrize("source, expected_type", [
    (1, basic_convertor), ("Мука", basic_convertor), (None, basic_convertor),
    (datetime(2026, 10, 22), datetime_convertor),
    ([], reference_convertor), ({}, reference_convertor),
    ((), reference_convertor), (group_model("Бакалея"), reference_convertor),
])
def test_selected_convertor_convert_factory_create_supported_type(source, expected_type):
    """<summary>Фабрика создаёт реализацию общего контракта по типу переданного значения.</summary>"""
    # Подготовка
    factory = convert_factory()

    # Действие
    result = factory.create(source)

    # Проверка
    assert isinstance(result, abstract_convertor)
    assert isinstance(result, expected_type)


def test_nested_structure_convert_factory_convert_mixed_containers():
    """<summary>Словари сохраняют ключи, tuple становится списком, все элементы преобразуются.</summary>"""
    # Подготовка
    source = {
        "rows": [SimpleNamespace(name="Мука", quantity=2), {"quantity": 0}],
        "dates": (datetime(2026, 10, 22), None),
        7: "numeric key",
        "": False,
        "empty": [],
    }

    factory = convert_factory()

    # Действие
    result = factory.convert(source)

    # Проверка
    assert result == {
        "value": {
            "rows": [{"name": "Мука", "quantity": 2}, {"quantity": 0}],
            "dates": ["2026-10-22T00:00:00", None],
            7: "numeric key", "": False, "empty": [],
        },
    }


def test_code_reference_convert_factory_convert_base_unit_self_cycle():
    """<summary>Самоссылка базового грамма заменяется кодом; остальные поля сохраняются.</summary>"""
    # Подготовка
    gram = unit_model("грамм")
    factory = convert_factory()

    # Действие
    result = factory.convert(gram, "unit")

    # Проверка
    assert result == {
        "unit": {
            "name": "грамм", "coefficient": 1,
            "unique_code": gram.unique_code,
            "base_unit": {"unique_code": gram.unique_code},
        },
    }


def test_full_shared_base_convert_factory_convert_units_in_separate_branches():
    """<summary>Килограмм и миллиграмм полностью раскрывают один заранее созданный грамм.</summary>"""
    # Подготовка
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    milligram = unit_model("миллиграмм", 0.001, gram)

    factory = convert_factory()
    expected_gram = {
        "name": "грамм", "coefficient": 1, "unique_code": gram.unique_code,
        "base_unit": {"unique_code": gram.unique_code},
    }

    # Действие
    result = factory.convert([kilogram, milligram])["value"]

    # Проверка
    assert result[0]["base_unit"] == expected_gram
    assert result[1]["base_unit"] == expected_gram
    assert result[0]["coefficient"] == 1000
    assert result[1]["coefficient"] == 0.001
    assert kilogram.base_unit is gram and milligram.base_unit is gram


def test_nested_recipe_convert_factory_convert_all_rows_and_computed_fields():
    """<summary>Рецепт сохраняет обе строки, общую группу, простые поля и расчётные массы.</summary>"""
    # Подготовка
    gram = unit_model("грамм")
    group = group_model("Бакалея")
    flour = item_model("Мука", "Мука пшеничная", group, gram)
    sugar = item_model("Сахар", "Сахар белый", group, gram)
    recipe = recipe_model("Тесто", gram, mass_coefficient=0.9)
    recipe.add_ingredient(flour, 200)
    recipe.add_ingredient(sugar, 100)

    factory = convert_factory()

    # Действие
    result = factory.convert(recipe, "recipe")["recipe"]

    # Проверка
    assert result["name"] == "Тесто"
    assert result["unique_code"] == recipe.unique_code
    assert result["mass_coefficient"] == 0.9
    assert result["gross_weight"] == 300
    assert result["net_weight"] == 270
    assert result["packaging_weight"] == 0
    assert len(result["ingredients"]) == 2
    for row, item, quantity in zip(result["ingredients"], [flour, sugar], [200, 100]):
        assert row["quantity"] == quantity
        assert row["is_packaging"] is False
        assert row["item"]["name"] == item.name
        assert row["item"]["full_name"] == item.full_name
        assert row["item"]["mass_ratio"] is None
        assert row["item"]["group"] == {
            "unique_code": group.unique_code, "name": "Бакалея",
        }
        assert row["item"]["unit"]["name"] == "грамм"


def test_nested_cake_convert_factory_convert_complex_recipe_with_shared_objects():
    """
    <summary>
    Торт с рецептами коржей и крема преобразуется вместе с датой и справочником
    единиц. Все строки, количества и расчётные массы сохраняются. Общие сахар,
    группа и грамм раскрываются в независимых ветках, самоссылка грамма
    заменяется кодом. Контекст очищается после завершения операции.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    milligram = unit_model("миллиграмм", 0.001, gram)
    piece = unit_model.create_piece()
    group = group_model.create_grocery()
    cake = recipe_item_model.create_cake(group, gram, piece)
    source = {
        "description": "Торт с вложенными рецептами коржей и крема",
        "created_at": datetime(
            2026, 10, 22, 18, 30, tzinfo=timezone(timedelta(hours=8)),
        ),
        "cake": cake,
        "units": [gram, kilogram, milligram],
    }
    factory = convert_factory()
    context = conversion_context_dto()
    expected_gram = {
        "name": "грамм", "coefficient": 1, "unique_code": gram.unique_code,
        "base_unit": {"unique_code": gram.unique_code},
    }
    expected_group = {"name": "Бакалея", "unique_code": group.unique_code}

    # Действие
    result = factory.convert(source, "example", context)

    # Проверка
    example = result["example"]
    converted_cake = example["cake"]
    recipe = converted_cake["recipe"]
    layers, cream = recipe["ingredients"]
    layers_recipe = layers["item"]["recipe"]
    cream_recipe = cream["item"]["recipe"]

    assert example["description"] == source["description"]
    assert example["created_at"] == "2026-10-22T18:30:00+08:00"
    assert converted_cake["name"] == "Бисквитный торт"
    assert converted_cake["unique_code"] == cake.unique_code
    assert converted_cake["output_quantity"] == 1
    assert converted_cake["group"] == expected_group
    assert recipe["name"] == "Сборка бисквитного торта"
    assert recipe["net_weight"] == 805
    assert recipe["gross_weight"] == 805
    assert recipe["packaging_weight"] == 0
    assert recipe["mass_unit"] == expected_gram
    assert layers["item"]["name"] == "Бисквитный корж"
    assert layers["quantity"] == 3
    assert cream["item"]["name"] == "Порция крема"
    assert cream["quantity"] == 1
    assert layers_recipe["gross_weight"] == 600
    assert layers_recipe["net_weight"] == 540
    assert cream_recipe["gross_weight"] == 400
    assert cream_recipe["net_weight"] == 400
    assert [
        (row["item"]["name"], row["quantity"])
        for row in layers_recipe["ingredients"]
    ] == [("Мука", 200), ("Сахар", 150), ("Яйцо", 250)]
    assert [
        (row["item"]["name"], row["quantity"])
        for row in cream_recipe["ingredients"]
    ] == [("Сметана", 300), ("Сахар", 100)]

    layers_sugar = layers_recipe["ingredients"][1]["item"]
    cream_sugar = cream_recipe["ingredients"][1]["item"]
    sugar = cake.recipe.ingredients[0].item.recipe.ingredients[1].item
    assert layers_sugar["unique_code"] == cream_sugar["unique_code"] == sugar.unique_code
    assert layers_sugar["group"] == cream_sugar["group"] == expected_group
    assert layers_sugar["unit"] == cream_sugar["unit"] == expected_gram
    assert example["units"][0] == expected_gram
    assert example["units"][1]["base_unit"] == expected_gram
    assert example["units"][2]["base_unit"] == expected_gram
    assert context.active_ids == set()
    assert context.path == []


def test_code_reference_convert_factory_convert_indirect_model_cycle():
    """<summary>Цикл из двух доменных экземпляров завершается ссылкой на первый код.</summary>"""
    # Подготовка
    first = abstract_model()
    second = abstract_model()
    first.link = second
    second.link = first

    factory = convert_factory()

    # Действие
    result = factory.convert(first)["value"]

    # Проверка
    assert result["link"]["unique_code"] == second.unique_code
    assert result["link"]["link"] == {"unique_code": first.unique_code}


def test_identity_tracking_convert_factory_convert_distinct_models_with_equal_codes():
    """<summary>Разные экземпляры с одинаковым unique_code не принимаются за цикл.</summary>"""
    # Подготовка
    first = abstract_model()
    second = abstract_model()
    second.unique_code = first.unique_code
    first.link = second
    second.name = "Вложенная модель"
    factory = convert_factory()

    # Действие
    result = factory.convert(first)["value"]["link"]

    # Проверка
    assert result == {
        "unique_code": first.unique_code, "name": "Вложенная модель",
    }


@pytest.mark.parametrize("kind", ["list", "dict", "object", "mixed"])
def test_arguments_exception_convert_factory_convert_cycle_without_code(kind):
    """<summary>Циклы коллекций и обычных объектов дают ошибку с путём и очищают контекст.</summary>"""
    # Подготовка
    if kind == "list":
        source = []
        source.append(source)
        expected_path = "root.0"
    elif kind == "dict":
        source = {}
        source["self"] = source
        expected_path = "root.self"
    elif kind == "object":
        source = SimpleNamespace()
        source.self = source
        expected_path = "root.self"
    else:
        source = {"rows": []}
        source["rows"].append(source)
        expected_path = "root.rows.0"
    context = conversion_context_dto()
    factory = convert_factory()

    # Действие
    with pytest.raises(arguments_exception) as error:
        factory.convert(source, "root", context)

    # Проверка
    assert expected_path in str(error.value)
    assert "Циклическая ссылка" in str(error.value)
    assert context.active_ids == set()
    assert context.path == []


def test_repeated_collection_convert_factory_convert_shared_list():
    """<summary>Одна коллекция полностью преобразуется в двух независимых ветках.</summary>"""
    # Подготовка
    shared = [1, {"name": "Мука"}]
    source = {"first": shared, "second": shared}

    factory = convert_factory()

    # Действие
    result = factory.convert(source)

    # Проверка
    assert result == {
        "value": {"first": [1, {"name": "Мука"}], "second": [1, {"name": "Мука"}]},
    }


@pytest.mark.parametrize("source", [b"data", {1, 2}, object()])
def test_arguments_exception_convert_factory_convert_unsupported_type(source):
    """<summary>Неподдерживаемые типы отклоняются вместо потери исходных данных.</summary>"""
    # Подготовка
    factory = convert_factory()

    # Действие
    with pytest.raises(arguments_exception) as error:
        factory.convert(source)

    # Проверка
    assert "не поддерживается" in str(error.value)


def test_shared_context_convert_factory_convert_independent_operations():
    """<summary>Вложения используют общий контекст, а повторный внешний вызов получает новый.</summary>"""
    # Подготовка
    factory = convert_factory()
    convertor = factory.create("flour")
    source = {"first": "flour", "second": ["sugar"]}

    # Действие
    with patch.object(convertor, "convert", wraps=convertor.convert) as convert:
        result = factory.convert(source)
        repeated_result = factory.convert(source)

    # Проверка
    assert result == {
        "value": {"first": "flour", "second": ["sugar"]},
    }
    assert repeated_result == result
    assert convert.call_count == 4
    contexts = [call.args[2] for call in convert.call_args_list]
    assert contexts[0] is contexts[1]
    assert contexts[2] is contexts[3]
    assert contexts[0] is not contexts[2]
    assert all(context.active_ids == set() and context.path == [] for context in contexts)
