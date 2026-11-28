"""Модульные проверки клонирования коллекции для поиска и сортировки."""

from operator import eq

import pytest

from Src.Core.exception import arguments_exception
from Src.Core.filter_operator_enum import filter_operator_enum
from Src.Core.sort_direction_enum import sort_direction_enum
from Src.Dtos.filter_dto import filter_dto
from Src.Dtos.filter_item_dto import filter_item_dto
from Src.Dtos.sort_item_dto import sort_item_dto
from Src.Logics.prototype import prototype
from Src.Models.group_model import group_model


def test_independent_clone_prototype_applies_supplied_dto():
    """<summary>Клон проверяет вложенное поле и сортирует результат, сохраняя исходную коллекцию.</summary>"""
    # Подготовка
    parent = group_model("Продукты")
    another = group_model("Упаковка")
    first = group_model("Апельсины", parent)
    second = group_model("Бобы", parent)
    outside = group_model("Стаканы", another)
    criteria = filter_dto(
        filters=(filter_item_dto(field="parent.name", operator=filter_operator_enum.EQUALS, value="Продукты"),),
        sort=(sort_item_dto(field="name", direction=sort_direction_enum.DESC),),
    )
    source = prototype(
        (first, outside, second), criteria, group_model,
        model_types=(group_model,), operators={filter_operator_enum.EQUALS: eq},
    )

    # Действие
    selected = source.clone()

    # Проверка
    assert selected is not source
    assert selected.data == (second, first)
    assert selected.data[0] is second
    assert source.data == (first, outside, second)


@pytest.mark.parametrize("criteria", [
    filter_dto(filters=(filter_item_dto(
        field="parent.missing.name", operator=filter_operator_enum.EQUALS, value="Продукты",
    ),)),
    filter_dto(sort=(sort_item_dto(field="parent.missing.name"),)),
])
def test_arguments_exception_clone_prototype_validates_paths_on_empty_data(criteria):
    """<summary>Даже пустой прототип отклоняет несуществующий путь фильтрации или сортировки.</summary>"""
    # Подготовка
    source = prototype(
        (), criteria, group_model,
        model_types=(group_model,), operators={filter_operator_enum.EQUALS: eq},
    )

    # Действие и проверка
    with pytest.raises(arguments_exception, match="parent.missing.name"):
        source.clone()
