"""Интеграционные тесты выгрузки и восстановления графа JSON с $id/$ref."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from Src.Dtos.conversion_context_dto import conversion_context_dto
from Src.Logics.convert_factory import convert_factory
from Src.Logics.reference_restore import reference_restore
from Src.Logics.storage_manager import storage_manager
from Src.Models.group_model import group_model
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.settings_model import settings_model
from Src.Models.unit_model import unit_model


def save_example(file_name: str, result: dict[str, object]) -> dict[str, object]:
    """Записывает пример в документацию и читает JSON для проверки восстановления."""
    directory = Path(__file__).resolve().parents[2] / "Docs" / "Examples" / "Conversion"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / file_name
    path.write_text(json.dumps(result, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


def test_saved_basic_types_convert_export_simple_values():
    """<summary>После выгрузки basic_types.json простые значения сохраняют содержимое и типы.</summary>"""
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
    restored = reference_restore().restore(saved, "example")
    # Проверка
    assert saved == result
    assert restored == source
    assert type(restored["quantity"]) is int
    assert type(restored["coefficient"]) is float
    assert restored["is_packaging"] is False
    assert restored["mass_ratio"] is None


def test_saved_datetime_convert_export_timezone_and_microseconds():
    """<summary>datetime.json восстанавливает datetime, смещение, микросекунды и обычную ISO-строку.</summary>"""
    # Подготовка
    source = {
        "without_timezone": datetime(2026, 10, 22, 18, 30),
        "with_timezone": datetime(2026, 10, 22, 18, 30, 15, 123456,
                                  tzinfo=timezone(timedelta(hours=8))),
        "utc": datetime(2026, 10, 22, 10, 30, tzinfo=timezone.utc),
        "text": "2026-10-22T18:30:00",
    }
    convertor = convert_factory().create(source)
    # Действие
    result = convertor.convert(source, "example")
    saved = save_example("datetime.json", result)
    restored = reference_restore().restore(saved, "example")
    # Проверка
    assert saved == result
    assert restored == source
    assert isinstance(restored["without_timezone"], datetime)
    assert isinstance(restored["text"], str)
    assert restored["with_timezone"].utcoffset() == timedelta(hours=8)
    assert restored["with_timezone"].microsecond == 123456


def test_saved_complex_recipe_convert_export_cake_and_shared_units():
    """
    <summary>
    complex_recipe.json восстанавливает торт с двумя рецептами, автоматически
    назначенными кодами, одним сахаром и общими единицами. Проверяется сохранение
    самоссылки грамма, масс и структуры при повторной сериализации.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    milligram = unit_model("миллиграмм", 0.001, gram)
    cake = recipe_item_model.create_cake(group_model.create_grocery(), gram, unit_model.create_piece())
    source = {
        "description": "Торт с вложенными рецептами коржей и крема",
        "created_at": datetime(2026, 10, 22, 18, 30, tzinfo=timezone(timedelta(hours=8))),
        "cake": cake, "units": [gram, kilogram, milligram],
    }
    convertor = convert_factory().create(source)
    context = conversion_context_dto()
    # Действие
    result = convertor.convert(source, "example", context)
    saved = save_example("complex_recipe.json", result)
    restored = reference_restore().restore(saved, "example")
    # Проверка
    assert saved == result
    restored_cake = restored["cake"]
    assert isinstance(restored_cake, recipe_item_model)
    assert restored_cake.unique_code == cake.unique_code
    assert restored_cake.recipe.net_weight == restored_cake.recipe.gross_weight == 805
    assert restored["created_at"] == source["created_at"]
    layers, cream = restored_cake.recipe.ingredients
    assert layers.quantity == 3
    assert cream.quantity == 1
    assert layers.item.recipe.net_weight == 540
    assert cream.item.recipe.net_weight == 400
    assert [(row.item.name, row.quantity) for row in layers.item.recipe.ingredients] == [
        ("Мука", 200), ("Сахар", 150), ("Яйцо", 250),
    ]
    assert [(row.item.name, row.quantity) for row in cream.item.recipe.ingredients] == [
        ("Сметана", 300), ("Сахар", 100),
    ]
    layers_sugar = layers.item.recipe.ingredients[1].item
    cream_sugar = cream.item.recipe.ingredients[1].item
    assert layers_sugar is cream_sugar
    assert layers_sugar.group is restored_cake.group
    assert layers_sugar.unit is restored["units"][0]
    assert restored["units"][0].base_unit is restored["units"][0]
    assert restored["units"][1].base_unit is restored["units"][0]
    assert restored["units"][2].base_unit is restored["units"][0]
    assert convertor.convert(restored, "example") == saved
    assert context.path == []


def test_saved_storage_convert_export_all_collections(monkeypatch):
    """
    <summary>
    storage.json содержит все коллекции storage_manager и восстанавливает их
    в отдельное хранилище. Проверяются коды, общие объекты, составные единицы,
    массы рецептов и независимость от действующего Singleton.
    </summary>
    """
    # Подготовка
    monkeypatch.setattr(storage_manager, "_storage_manager__instance", None)
    storage = storage_manager(settings_model())
    convertor = convert_factory().create(storage)
    collections = {
        "warehouses": storage.warehouses, "groups": storage.groups,
        "units": storage.units, "items": storage.items,
    }
    # Действие
    result = convertor.convert(storage, "storage")
    saved = save_example("storage.json", result)
    restored = reference_restore().restore(saved, "storage")
    # Проверка
    assert saved == result
    assert isinstance(restored, storage_manager)
    assert restored is not storage
    assert storage_manager(settings_model()) is storage
    for name, models in collections.items():
        actual = getattr(restored, name)
        assert len(actual) == len(models)
        assert [row.unique_code for row in actual] == [model.unique_code for model in models]
        assert [row.name for row in actual] == [model.name for model in models]
        assert all(UUID(hex=row.unique_code).version == 4 for row in actual)
    units = {unit.unique_code: unit for unit in restored.units}
    groups = {group.unique_code: group for group in restored.groups}
    for original in storage.units:
        unit = units[original.unique_code]
        assert unit.coefficient == original.coefficient
        assert unit.base_unit is units[original.base_unit.unique_code]
    for item in restored.items:
        assert item.group is groups[item.group.unique_code]
        assert item.unit is units[item.unit.unique_code]
    for original, item in zip(storage.items, restored.items):
        assert item.calculate_mass(1, restored.units[0]) == original.calculate_mass(1, storage.units[0])
    cake = next(item for item in restored.items if item.name == "Бисквитный торт")
    assert cake.recipe.net_weight == 805
    layers, cream = cake.recipe.ingredients
    assert layers.item.recipe.ingredients[1].item is cream.item.recipe.ingredients[1].item
    assert convertor.convert(restored, "storage") == saved
