"""Юнит-тесты модели единицы измерения."""

import pytest

from Src.Core.abstract_model import abstract_model
from Src.Core.exception import arguments_exception
from Src.Models.unit_model import unit_model



def test_created_unit_model_default_base_unit():
    """
    <summary>
    Единица, созданная только с именем, является базовой.
    Её коэффициент равен 1, а базовая единица — сам объект.
    </summary>
    """
    # Действие
    unit = unit_model("грамм")

    # Проверка
    assert isinstance(unit, abstract_model)
    assert unit.unique_code != ""
    assert unit.name == "грамм"
    assert unit.coefficient == 1
    assert unit.base_unit is unit


def test_created_unit_model_explicit_base_coefficient():
    """
    <summary>
    Базовую единицу можно создать с явно указанным коэффициентом 1.
    Наименование сохраняется без пробелов по краям.
    </summary>
    """
    # Действие
    unit = unit_model("  грамм  ", 1)

    # Проверка
    assert unit.name == "грамм"
    assert unit.coefficient == 1
    assert unit.base_unit is unit


@pytest.mark.parametrize(
    "name, coefficient",
    [
        ("килограмм", 1000),
        ("миллиграмм", 0.001),
        ("грамм для учёта", 1),
    ],
)
def test_created_unit_model_valid_derived_unit(name, coefficient):
    """
    <summary>
    Производная единица сохраняет имя, положительный коэффициент
    и ссылку на переданную базовую единицу.
    Допускаются целые, дробные коэффициенты и коэффициент 1.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")

    # Действие
    unit = unit_model(name, coefficient, gram)

    # Проверка
    assert unit.name == name
    assert unit.coefficient == coefficient
    assert unit.base_unit is gram


@pytest.mark.parametrize(
    "coefficient",
    [
        0,
        -1,
        -0.001,
        "1000",
        None,
        True,
        False,
        float("inf"),
        float("-inf"),
        float("nan"),
    ],
)
def test_arguments_exception_unit_model_invalid_coefficient(coefficient):
    """
    <summary>
    Нулевой, отрицательный, нечисловой или неконечный коэффициент
    вызывает arguments_exception с указанием поля coefficient.
    Логические значения не принимаются как числа.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")

    # Действие
    with pytest.raises(arguments_exception) as error:
        unit_model("килограмм", coefficient, gram)

    # Проверка
    assert "Поле: coefficient" in str(error.value)


@pytest.mark.parametrize(
    "base_unit", ["грамм", 123, object()]
)
def test_arguments_exception_unit_model_invalid_base_unit(base_unit):
    """
    <summary>
    Базовая единица неверного типа вызывает arguments_exception
    с указанием поля base_unit.
    </summary>
    """
    # Действие
    with pytest.raises(arguments_exception) as error:
        unit_model("килограмм", 1000, base_unit)

    # Проверка
    assert "Поле: base_unit" in str(error.value)


def test_arguments_exception_unit_model_derived_base_unit():
    """
    <summary>
    Производную единицу нельзя использовать как базовую.
    Создание цепочки производных единиц вызывает arguments_exception.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)

    # Действие
    with pytest.raises(arguments_exception) as error:
        unit_model("тонна", 1000, kilogram)

    # Проверка
    assert "Поле: base_unit" in str(error.value)


@pytest.mark.parametrize("coefficient", [1000, 0.001])
def test_arguments_exception_unit_model_non_unit_base_coefficient(
    coefficient,
):
    """
    <summary>
    Без ссылки на базовую единицу допускается только коэффициент 1.
    Другой коэффициент вызывает arguments_exception.
    </summary>
    """
    # Действие
    with pytest.raises(arguments_exception) as error:
        unit_model("единица", coefficient)

    # Проверка
    assert "Поле: coefficient" in str(error.value)


def test_arguments_exception_unit_model_invalid_name():
    """
    <summary>
    Конструктор единицы измерения использует общую проверку имени.
    Пустое имя вызывает arguments_exception с указанием поля name.
    </summary>
    """
    # Действие
    with pytest.raises(arguments_exception) as error:
        unit_model("")

    # Проверка
    assert "Поле: name" in str(error.value)


def test_converted_quantity_unit_model_kilograms_to_grams():
    """
    <summary>
    Демонстрируется пересчёт количества в базовую единицу:
    два килограмма соответствуют двум тысячам граммов.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм", 1)
    kilogram = unit_model("килограмм", 1000, gram)
    quantity = 2

    # Действие
    quantity_in_grams = quantity * kilogram.coefficient

    # Проверка
    assert kilogram.base_unit is gram
    assert quantity_in_grams == 2000