"""Юнит-тесты массы через обычные и составные единицы."""

import pytest

from Src.Core.exception import arguments_exception
from Src.Models.unit_model import unit_model
from Src.Models.ratio_unit_model import ratio_unit_model
from Src.Models.ratio_value_model import ratio_value_model


def test_calculated_mass_convert_to_flour():
    """
    <summary>
    0.3 килограмма муки соответствуют 300 граммам.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)

    # Действие
    result = kilogram.convert_to(0.3, gram)

    # Проверка
    assert result == pytest.approx(300)


def test_calculated_mass_calculate_mass_liquid():
    """
    <summary>
    100 мл при плотности 0.9 кг/л дают 90 г.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    milliliter = unit_model("миллилитр")
    liter = unit_model("литр", 1000, milliliter)
    density = ratio_value_model(
        0.9, ratio_unit_model.kilograms_per_liter(kilogram, liter)
    )

    # Действие
    result = density.calculate_mass(100, milliliter, gram)

    # Проверка
    assert result == pytest.approx(90)

    # Действие
    second_result = density.calculate_mass(0, milliliter, gram)

    # Проверка
    assert second_result == 0


def test_calculated_mass_calculate_mass_packaging():
    """
    <summary>
    Две упаковки по 0.015 кг дают массу 30 г.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    piece = unit_model("штука")
    weight = ratio_value_model(
        0.015, ratio_unit_model.kilograms_per_piece(kilogram, piece)
    )

    # Действие
    result = weight.calculate_mass(2, piece, gram)

    # Проверка
    assert result == pytest.approx(30)
    assert weight.value == pytest.approx(0.015)
    assert weight.unit.numerator_unit is kilogram


def test_arguments_exception_ratio_value_model_zero_value():
    """
    <summary>
    Плотность или масса штуки должны быть положительными.
    </summary>
    """
    # Подготовка
    unit = ratio_unit_model(unit_model("грамм"), unit_model("штука"))

    # Действие
    with pytest.raises(arguments_exception) as error:
        ratio_value_model(0, unit)

    # Проверка
    assert "Поле: value" in str(error.value)


def test_arguments_exception_calculate_mass_negative_quantity():
    """
    <summary>
    Расчёт отклоняет отрицательное количество.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    piece = unit_model("штука")
    weight = ratio_value_model(15, ratio_unit_model.grams_per_piece(gram, piece))

    # Действие
    with pytest.raises(arguments_exception) as error:
        weight.calculate_mass(-1, piece, gram)

    # Проверка
    assert "Поле: quantity" in str(error.value)


def test_arguments_exception_calculate_mass_incompatible_quantity():
    """
    <summary>
    Массу штуки нельзя применить к объёму.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    piece = unit_model("штука")
    weight = ratio_value_model(15, ratio_unit_model.grams_per_piece(gram, piece))

    # Действие
    with pytest.raises(arguments_exception) as error:
        weight.calculate_mass(2, unit_model("миллилитр"), gram)

    # Проверка
    assert "Поле: target_unit" in str(error.value)


def test_arguments_exception_calculate_mass_incompatible_target():
    """
    <summary>
    Результат массы нельзя вернуть в единицах объёма.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    piece = unit_model("штука")
    weight = ratio_value_model(15, ratio_unit_model.grams_per_piece(gram, piece))

    # Действие
    with pytest.raises(arguments_exception) as error:
        weight.calculate_mass(2, piece, unit_model("миллилитр"))

    # Проверка
    assert "Поле: target_unit" in str(error.value)
