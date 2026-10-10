"""Юнит-тесты массы через обычные и составные единицы."""

import pytest

from Src.Core.exception import arguments_exception
from Src.Models.unit_model import unit_model
from Src.Models.ratio_unit_model import ratio_unit_model
from Src.Models.ratio_value_model import ratio_value_model


def test_calculated_mass_convert_to_flour():
    """<summary>0.3 килограмма муки соответствуют 300 граммам.</summary>"""
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)

    assert kilogram.convert_to(0.3, gram) == pytest.approx(300)


def test_calculated_mass_calculate_mass_liquid():
    """<summary>100 мл при плотности 0.9 кг/л дают 90 г.</summary>"""
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    milliliter = unit_model("миллилитр")
    liter = unit_model("литр", 1000, milliliter)
    density = ratio_value_model(
        0.9, ratio_unit_model.kilograms_per_liter(kilogram, liter)
    )

    assert density.calculate_mass(100, milliliter, gram) == pytest.approx(90)
    assert density.calculate_mass(0, milliliter, gram) == 0


def test_calculated_mass_calculate_mass_packaging():
    """<summary>Две упаковки по 0.015 кг дают массу 30 г.</summary>"""
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    piece = unit_model("штука")
    weight = ratio_value_model(
        0.015, ratio_unit_model.kilograms_per_piece(kilogram, piece)
    )

    assert weight.calculate_mass(2, piece, gram) == pytest.approx(30)
    assert weight.value == pytest.approx(0.015)
    assert weight.unit.numerator_unit is kilogram


def test_arguments_exception_ratio_value_model_zero_value():
    """<summary>Плотность или масса штуки должны быть положительными.</summary>"""
    unit = ratio_unit_model(unit_model("грамм"), unit_model("штука"))

    with pytest.raises(arguments_exception):
        ratio_value_model(0, unit)


def test_arguments_exception_calculate_mass_negative_quantity():
    """<summary>Расчёт отклоняет отрицательное количество.</summary>"""
    gram = unit_model("грамм")
    piece = unit_model("штука")
    weight = ratio_value_model(15, ratio_unit_model.grams_per_piece(gram, piece))

    with pytest.raises(arguments_exception):
        weight.calculate_mass(-1, piece, gram)


def test_arguments_exception_calculate_mass_incompatible_quantity():
    """<summary>Массу штуки нельзя применить к объёму.</summary>"""
    gram = unit_model("грамм")
    piece = unit_model("штука")
    weight = ratio_value_model(15, ratio_unit_model.grams_per_piece(gram, piece))

    with pytest.raises(arguments_exception):
        weight.calculate_mass(2, unit_model("миллилитр"), gram)


def test_arguments_exception_calculate_mass_incompatible_target():
    """<summary>Результат массы нельзя вернуть в единицах объёма.</summary>"""
    gram = unit_model("грамм")
    piece = unit_model("штука")
    weight = ratio_value_model(15, ratio_unit_model.grams_per_piece(gram, piece))

    with pytest.raises(arguments_exception):
        weight.calculate_mass(2, piece, unit_model("миллилитр"))
