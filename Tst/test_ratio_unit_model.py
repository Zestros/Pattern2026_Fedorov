"""Юнит-тесты составных единиц измерения."""

import pytest

from Src.Core.exception import arguments_exception
from Src.Models.unit_model import unit_model
from Src.Models.ratio_unit_model import ratio_unit_model


def test_converted_value_convert_to_grams_per_liter():
    """
    <summary>
    0.9 г/мл переводятся в 900 г/л и обратно.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    milliliter = unit_model("миллилитр")
    liter = unit_model("литр", 1000, milliliter)
    source = ratio_unit_model.grams_per_milliliter(gram, milliliter)
    target = ratio_unit_model(gram, liter)

    # Действие
    result = source.convert_to(0.9, target)

    # Проверка
    assert result == pytest.approx(900)

    # Действие
    second_result = target.convert_to(900, source)

    # Проверка
    assert second_result == pytest.approx(0.9)


def test_converted_value_convert_to_kilograms_per_liter():
    """
    <summary>
    При переводе г/мл в кг/л учитываются обе единицы.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    milliliter = unit_model("миллилитр")
    liter = unit_model("литр", 1000, milliliter)
    source = ratio_unit_model.grams_per_milliliter(gram, milliliter)
    target = ratio_unit_model.kilograms_per_liter(kilogram, liter)

    # Действие
    result = source.convert_to(0.9, target)

    # Проверка
    assert result == pytest.approx(0.9)
    assert target.numerator_unit is kilogram
    assert target.denominator_unit is liter


def test_arguments_exception_convert_to_incompatible_denominator():
    """
    <summary>
    Плотность нельзя перевести в массу одной штуки.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    source = ratio_unit_model(gram, unit_model("миллилитр"))
    target = ratio_unit_model.grams_per_piece(gram, unit_model("штука"))

    # Действие
    with pytest.raises(arguments_exception) as error:
        source.convert_to(1, target)

    # Проверка
    assert "Поле: target_unit" in str(error.value)


def test_arguments_exception_convert_to_incompatible_numerator():
    """
    <summary>
    Несовместимые единицы числителя отклоняются.
    </summary>
    """
    # Подготовка
    piece = unit_model("штука")
    source = ratio_unit_model(unit_model("грамм"), piece)
    target = ratio_unit_model(unit_model("метр"), piece)

    # Действие
    with pytest.raises(arguments_exception) as error:
        source.convert_to(1, target)

    # Проверка
    assert "Поле: target_unit" in str(error.value)
