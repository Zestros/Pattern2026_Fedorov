from pathlib import Path

import connexion
from flask import Response

from Src.Core.report_type_enum import report_type_enum
from Src.Logics.settings_manager import setting_manager
from Src.Logics.storage_manager import storage_manager
from Src.Logics.report_factory import report_factory
from Src.Models.recipe_item_model import recipe_item_model


settings = setting_manager()
settings.load(str(Path(__file__).with_name("settings.json")))

storage = storage_manager(settings.settings)
factory = report_factory()

api = connexion.FlaskApp(__name__, specification_dir="./")

@api.route("/api/get_report", methods=["GET"])
def get_report():
    """Формирует текстовый отчёт по стартовому рецепту лепёшек."""
    product = next(
        (
            item
            for item in storage.items
            if isinstance(item, recipe_item_model)
            and item.name == "Пшеничные лепёшки"
        ),
        None,
    )

    if product is None:
        return Response(
            "Рецепт не найден",
            status=404,
            content_type="text/plain; charset=utf-8",
        )

    report = factory.create(report_type_enum.TXT)
    result = report.build(product.recipe)

    return Response(
        result.text,
        content_type="text/plain; charset=utf-8",
    )


if __name__ == "__main__":
    api.run(host="0.0.0.0", port=8000)

