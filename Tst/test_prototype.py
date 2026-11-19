"""Модульные проверки клонирования коллекции для поиска и сортировки."""

from operator import eq

from Src.Core.filter_criteria import filter_criteria, filter_item, sort_direction_enum, sort_item
from Src.Logics.prototype import prototype
from Src.Models.group_model import group_model


def test_independent_clone_prototype_applies_supplied_criteria():
    """<summary>Клон проверяет вложенное поле и сортирует результат, сохраняя исходную коллекцию.</summary>"""
    # Подготовка
    parent = group_model("Продукты")
    another = group_model("Упаковка")
    first = group_model("Апельсины", parent)
    second = group_model("Бобы", parent)
    outside = group_model("Стаканы", another)
    criteria = filter_criteria(
        filters=(filter_item(("parent", "name"), eq, "Продукты"),),
        sort=(sort_item(("name",), sort_direction_enum.DESC),),
    )
    source = prototype((first, outside, second), criteria)

    # Действие
    selected = source.clone()

    # Проверка
    assert selected is not source
    assert selected.data == (second, first)
    assert selected.data[0] is second
    assert source.data == (first, outside, second)
