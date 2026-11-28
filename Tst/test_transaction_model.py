"""Модульные проверки входных данных и количества складского движения."""

from datetime import datetime

import pytest

from Src.Core.exception import arguments_exception
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.transaction_model import transaction_model
from Src.Models.unit_model import unit_model
from Src.Models.warehouse_model import warehouse_model


@pytest.mark.parametrize("quantity", [0, False, float("nan"), float("inf"), "5"])
def test_arguments_exception_transaction_model_rejects_invalid_quantity(quantity):
    """<summary>Модель отклоняет нулевое, нечисловое и неконечное количество движения.</summary>"""
    # Подготовка
    unit = unit_model.create_kilogram()
    item = item_model.create_flour(group_model.create_grocery(), unit)
    warehouse = warehouse_model.create_main()

    # Действие и проверка
    with pytest.raises(arguments_exception, match="Поле: quantity"):
        transaction_model(datetime(2026, 2, 1), warehouse, item, unit, quantity)
