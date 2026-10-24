"""Интеграционные тесты преобразования объектов и выгрузки примеров JSON."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from Src.Dtos.conversion_context_dto import conversion_context_dto
from Src.Logics.convert_factory import convert_factory
from Src.Models.group_model import group_model
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.unit_model import unit_model


def save_example(file_name: str, result: dict[str, object]) -> dict[str, object]:
    """Записывает пример в документацию и возвращает прочитанный из файла JSON."""
    directory = Path(__file__).resolve().parents[2] / "Docs" / "Examples" / "Conversion"
    directory.mkdir(parents=True, exist_ok=True)
    output_path = directory / file_name
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=4) + "\n", encoding="utf-8",
    )
    return json.loads(output_path.read_text(encoding="utf-8"))


def test_saved_basic_types_convert_export_simple_values():
    """
    <summary>
    Простые значения преобразуются выбранным конвертором и сохраняются
    в basic_types.json. После чтения JSON числа, строки, bool и None сохраняются.
    </summary>
    """
    # Подготовка
    source = {
        "name": "Мука", "quantity": 2, "coefficient": 0.9, "zero": 0,
        "empty_string": "", "is_available": True, "is_packaging": False,
        "mass_ratio": None,
    }
    convertor = convert_factory().create(source)

    # Действие
    result = convertor.convert(source, "example")
    saved = save_example("basic_types.json", result)

    # Проверка
    assert saved == result == {"example": source}
    assert type(saved["example"]["quantity"]) is int
    assert type(saved["example"]["coefficient"]) is float
    assert saved["example"]["is_packaging"] is False
    assert saved["example"]["mass_ratio"] is None


def test_saved_datetime_convert_export_timezone_and_microseconds():
    """
    <summary>
    Даты внутри словаря сохраняются в datetime.json строками ISO 8601.
    Проверяются отсутствие пояса, исходное смещение, UTC и микросекунды.
    </summary>
    """
    # Подготовка
    source = {
        "without_timezone": datetime(2026, 10, 22, 18, 30),
        "with_timezone": datetime(
            2026, 10, 22, 18, 30, 15, 123456,
            tzinfo=timezone(timedelta(hours=8)),
        ),
        "utc": datetime(2026, 10, 22, 10, 30, tzinfo=timezone.utc),
    }
    convertor = convert_factory().create(source)

    # Действие
    result = convertor.convert(source, "example")
    saved = save_example("datetime.json", result)

    # Проверка
    assert saved == result == {
        "example": {
            "without_timezone": "2026-10-22T18:30:00",
            "with_timezone": "2026-10-22T18:30:15.123456+08:00",
            "utc": "2026-10-22T10:30:00+00:00",
        },
    }


def test_saved_complex_recipe_convert_export_cake_and_shared_units():
    """
    <summary>
    Торт с двумя вложенными рецептами сохраняется в complex_recipe.json
    с кодами, назначенными моделями. Проверяются состав, массы, общий сахар,
    полные данные общего грамма в разных ветках и null для его самоссылки.
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
    convertor = convert_factory().create(source)
    context = conversion_context_dto()
    expected_gram = {
        "name": "грамм", "coefficient": 1, "unique_code": gram.unique_code,
        "base_unit": None,
    }

    # Действие
    result = convertor.convert(source, "example", context)
    saved = save_example("complex_recipe.json", result)

    # Проверка
    assert saved == result
    example = saved["example"]
    recipe = example["cake"]["recipe"]
    layers, cream = recipe["ingredients"]
    layers_recipe = layers["item"]["recipe"]
    cream_recipe = cream["item"]["recipe"]
    assert example["cake"]["unique_code"] == cake.unique_code
    assert example["created_at"] == "2026-10-22T18:30:00+08:00"
    assert recipe["net_weight"] == recipe["gross_weight"] == 805
    assert recipe["mass_unit"] == expected_gram
    assert layers["quantity"] == 3
    assert cream["quantity"] == 1
    assert layers_recipe["net_weight"] == 540
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
    assert layers_sugar == cream_sugar
    assert layers_sugar["unique_code"] == sugar.unique_code
    assert layers_sugar["unit"] == expected_gram
    assert layers_sugar["group"] == {
        "name": "Бакалея", "unique_code": group.unique_code,
    }
    assert example["units"][0] == expected_gram
    assert example["units"][1] == {
        "name": "килограмм", "coefficient": 1000,
        "unique_code": kilogram.unique_code, "base_unit": expected_gram,
    }
    assert example["units"][2] == {
        "name": "миллиграмм", "coefficient": 0.001,
        "unique_code": milligram.unique_code, "base_unit": expected_gram,
    }
    assert context.active_ids == set()
    assert context.path == []
