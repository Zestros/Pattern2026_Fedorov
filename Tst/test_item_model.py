"""Юнит-тесты модели номенклатуры."""

import pytest

from Src.Core.abstract_model import abstract_model
from Src.Core.exception import arguments_exception
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.unit_model import unit_model


def test_created_item_model_valid_parameters():
    """
    <summary>
    Номенклатура сохраняет наименования, группу и единицу измерения.
    Пробелы по краям наименований удаляются.
    Модель наследует абстрактную базу и получает уникальный код.
    </summary>
    """
    # Подготовка
    group = group_model("Молочные продукты")
    unit = unit_model("литр")

    # Действие
    item = item_model(
        "  Молоко  ",
        "  Молоко питьевое 3,2%  ",
        group,
        unit,
    )

    # Проверка
    assert isinstance(item, abstract_model)
    assert item.unique_code != ""
    assert item.name == "Молоко"
    assert item.full_name == "Молоко питьевое 3,2%"
    assert item.group is group
    assert item.unit is unit


@pytest.mark.parametrize("full_name", ["А", "А" * 255, "  " + "А" * 255 + "  "])
def test_created_item_model_full_name_boundary(full_name):
    """
    <summary>
    Полное наименование длиной от 1 до 255 символов допускается.
    Длина проверяется после удаления пробелов по краям.
    </summary>
    """
    # Подготовка
    group = group_model("Продукты")
    unit = unit_model("штука")

    # Действие
    item = item_model("Товар", full_name, group, unit)

    # Проверка
    assert item.full_name == full_name.strip()


@pytest.mark.parametrize(
    "field, value",
    [
        ("name", ""),
        ("full_name", ""),
        ("full_name", "   "),
        ("full_name", "А" * 256),
        ("full_name", None),
        ("full_name", 123),
        ("group", None),
        ("group", "Продукты"),
        ("group", unit_model("штука")),
        ("unit", None),
        ("unit", "килограмм"),
        ("unit", group_model("Продукты")),
    ],
)
def test_arguments_exception_item_model_invalid_parameters(field, value):
    """
    <summary>
    Недопустимый параметр конструктора вызывает arguments_exception.
    Исключение содержит название соответствующего поля.
    Группа и единица измерения не могут подменять друг друга.
    </summary>
    """
    # Подготовка
    parameters = {
        "name": "Товар",
        "full_name": "Полное наименование товара",
        "group": group_model("Продукты"),
        "unit": unit_model("штука"),
    }
    parameters[field] = value

    # Действие
    with pytest.raises(arguments_exception) as error:
        item_model(**parameters)

    # Проверка
    assert f"Поле: {field}" in str(error.value)


def test_updated_properties_item_model_valid_assignment():
    """
    <summary>
    Полное наименование, группу и единицу можно изменить.
    Новые связи сохраняют ссылки на переданные объекты.
    </summary>
    """
    # Подготовка
    item = item_model(
        "Молоко",
        "Молоко питьевое",
        group_model("Продукты"),
        unit_model("штука"),
    )
    new_group = group_model("Молочные продукты")
    new_unit = unit_model("литр")

    # Действие
    item.full_name = "  Молоко питьевое 3,2%  "
    item.group = new_group
    item.unit = new_unit

    # Проверка
    assert item.full_name == "Молоко питьевое 3,2%"
    assert item.group is new_group
    assert item.unit is new_unit


@pytest.mark.parametrize(
    "field, value",
    [
        ("full_name", ""),
        ("full_name", "   "),
        ("full_name", "А" * 256),
        ("full_name", None),
        ("full_name", 123),
        ("group", None),
        ("group", "Продукты"),
        ("unit", None),
        ("unit", "килограмм"),
    ],
)
def test_unchanged_property_item_model_invalid_assignment(field, value):
    """
    <summary>
    Ошибочное присваивание вызывает arguments_exception с названием поля.
    Прежнее значение свойства сохраняется.
    </summary>
    """
    # Подготовка
    item = item_model(
        "Товар",
        "Полное наименование товара",
        group_model("Продукты"),
        unit_model("штука"),
    )
    previous_value = getattr(item, field)

    # Действие
    with pytest.raises(arguments_exception) as error:
        setattr(item, field, value)

    # Проверка
    assert f"Поле: {field}" in str(error.value)
    assert getattr(item, field) is previous_value


def test_converted_quantity_item_model_assigned_unit():
    """
    <summary>
    Номенклатура использует производную единицу измерения.
    Три килограмма муки соответствуют трём тысячам граммов.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    item = item_model(
        "Мука",
        "Мука пшеничная высшего сорта",
        group_model("Бакалея"),
        kilogram,
    )

    # Действие
    quantity_in_base = 3 * item.unit.coefficient

    # Проверка
    assert item.unit.base_unit is gram
    assert quantity_in_base == 3000