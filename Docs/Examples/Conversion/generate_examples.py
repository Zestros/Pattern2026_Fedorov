"""Создаёт три демонстрационных JSON рядом с этим скриптом.

basic_types.json — числа, строки, bool и None.
datetime.json — даты без часового пояса и с часовым поясом.
complex_recipe.json — торт с вложенными рецептами и общими объектами.
При повторном запуске файлы перезаписываются теми же данными.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from Src.Logics.convert_factory import convert_factory
from Src.Models.group_model import group_model
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.unit_model import unit_model


def create_complex_recipe() -> dict[str, object]:
    """Создаёт торт с коржами, кремом и общим граммом для нескольких единиц."""
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    milligram = unit_model("миллиграмм", 0.001, gram)
    piece = unit_model.create_piece()
    group = group_model.create_grocery()
    cake = recipe_item_model.create_cake(group, gram, piece)
    layers, cream = cake.recipe.ingredients
    flour_row, sugar_row, eggs_row = layers.item.recipe.ingredients
    sour_cream_row, shared_sugar_row = cream.item.recipe.ingredients

    models = [
        gram, kilogram, milligram, piece, group, cake, cake.recipe,
        layers, cream, layers.item, layers.item.recipe,
        cream.item, cream.item.recipe,
        flour_row, sugar_row, eggs_row, sour_cream_row, shared_sugar_row,
        flour_row.item, sugar_row.item, eggs_row.item, sour_cream_row.item,
    ]
    for index, model in enumerate(models, start=1):
        model.unique_code = f"{index:032x}"

    return {
        "description": "Торт с вложенными рецептами коржей и крема",
        "created_at": datetime(
            2026, 10, 22, 18, 30, tzinfo=timezone(timedelta(hours=8)),
        ),
        "cake": cake,
        "units": [gram, kilogram, milligram],
    }


def main() -> None:
    """Преобразует три примера фабрикой и сохраняет читаемые JSON-файлы."""
    examples = {
        "basic_types.json": {
            "name": "Мука",
            "quantity": 2,
            "coefficient": 0.9,
            "zero": 0,
            "empty_string": "",
            "is_available": True,
            "is_packaging": False,
            "mass_ratio": None,
        },
        "datetime.json": {
            "without_timezone": datetime(2026, 10, 22, 18, 30),
            "with_timezone": datetime(
                2026, 10, 22, 18, 30, 15, 123456,
                tzinfo=timezone(timedelta(hours=8)),
            ),
            "utc": datetime(2026, 10, 22, 10, 30, tzinfo=timezone.utc),
        },
        "complex_recipe.json": create_complex_recipe(),
    }
    factory = convert_factory()
    output_directory = Path(__file__).resolve().parent

    for file_name, source in examples.items():
        result = factory.convert(source, "example")
        output_path = output_directory / file_name
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=4) + "\n",
            encoding="utf-8",
        )
        print(f"Создан: {output_path}")


if __name__ == "__main__":
    main()
