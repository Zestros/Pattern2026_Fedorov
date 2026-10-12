"""Юнит-тесты расчёта массы непосредственно в номенклатуре"""

import pytest

from Src.Core.exception import arguments_exception
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.unit_model import unit_model
from Src.Models.ratio_unit_model import ratio_unit_model
from Src.Models.ratio_value_model import ratio_value_model


def test_calculated_mass_calculate_mass_flour():
    """
    <summary>
    0.3 кг муки дают 300 г без дополнительной характеристики.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)

    # Действие
    flour = item_model("Мука", "Мука пшеничная", group_model("Бакалея"), kilogram)

    # Проверка
    assert flour.mass_ratio is None

    # Действие
    result = flour.calculate_mass(0.3, gram)

    # Проверка
    assert result == pytest.approx(300)

    # Действие
    second_result = flour.calculate_mass(0, gram)

    # Проверка
    assert second_result == 0


def test_calculated_mass_calculate_mass_liquid():
    """
    <summary>
    Плотность 0.9 кг/л применяется к литрам учёта и явно заданным мл.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    milliliter = unit_model("миллилитр")
    liter = unit_model("литр", 1000, milliliter)
    oil = item_model(
        "Масло", "Масло растительное", group_model("Бакалея"), liter,
        mass_ratio=ratio_value_model(
            0.9, ratio_unit_model.kilograms_per_liter(kilogram, liter)
        ),
    )

    # Действие
    result = oil.calculate_mass(0.1, gram)

    # Проверка
    assert result == pytest.approx(90)

    # Действие
    second_result = oil.calculate_mass(100, gram, milliliter)

    # Проверка
    assert second_result == pytest.approx(90)


def test_calculated_mass_calculate_mass_packaging():
    """
    <summary>
    Две упаковки по 15 г дают 30 г; замена характеристики меняет расчёт.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    piece = unit_model("штука")
    ratio_unit = ratio_unit_model.grams_per_piece(gram, piece)
    box = item_model(
        "Контейнер", "Контейнер для блюда", group_model("Упаковка"), piece,
        mass_ratio=ratio_value_model(15, ratio_unit),
    )

    # Действие
    result = box.calculate_mass(2, gram)

    # Проверка
    assert result == pytest.approx(30)

    # Действие
    box.mass_ratio = ratio_value_model(20, ratio_unit)

    # Действие
    second_result = box.calculate_mass(2, gram)

    # Проверка
    assert second_result == pytest.approx(40)


def test_arguments_exception_calculate_mass_missing_ratio():
    """
    <summary>
    Без плотности объём нельзя перевести в массу, включая после её удаления.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    milliliter = unit_model("миллилитр")
    oil = item_model("Масло", "Масло растительное", group_model("Бакалея"), milliliter)
    oil.mass_ratio = ratio_value_model(
        0.9, ratio_unit_model.grams_per_milliliter(gram, milliliter)
    )

    # Действие
    oil.mass_ratio = None

    # Проверка
    assert oil.mass_ratio is None

    # Действие
    with pytest.raises(arguments_exception):
        oil.calculate_mass(100, gram)

    # Проверка
    # pytest.raises проверяет ожидаемый тип исключения.


def test_preserved_ratio_mass_ratio_invalid_assignment():
    """
    <summary>
    Неверный тип характеристики отклоняется без потери прежнего значения.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    piece = unit_model("штука")
    box = item_model("Контейнер", "Контейнер для блюда", group_model("Упаковка"), piece)
    ratio = ratio_value_model(15, ratio_unit_model.grams_per_piece(gram, piece))
    box.mass_ratio = ratio

    # Действие
    with pytest.raises(arguments_exception) as error:
        box.mass_ratio = 15

    # Проверка
    # pytest.raises проверяет ожидаемый тип исключения.
    assert "Поле: mass_ratio" in str(error.value)
    assert box.mass_ratio is ratio


def test_arguments_exception_calculate_mass_incompatible_ratio():
    """
    <summary>
    Характеристика г/шт не позволяет рассчитать массу объёма в мл.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    milliliter = unit_model("миллилитр")
    piece = unit_model("штука")
    oil = item_model("Масло", "Масло растительное", group_model("Бакалея"), milliliter)
    oil.mass_ratio = ratio_value_model(15, ratio_unit_model.grams_per_piece(gram, piece))

    # Действие
    with pytest.raises(arguments_exception) as error:
        oil.calculate_mass(100, gram)

    # Проверка
    assert "Поле: target_unit" in str(error.value)


def test_arguments_exception_calculate_mass_negative_quantity():
    """
    <summary>
    Расчёт массы использует существующую проверку количества.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    flour = item_model("Мука", "Мука пшеничная", group_model("Бакалея"), gram)

    # Действие
    with pytest.raises(arguments_exception) as error:
        flour.calculate_mass(-1, gram)

    # Проверка
    # pytest.raises проверяет ожидаемый тип исключения.
    assert "Поле: quantity" in str(error.value)

    # Проверка
    assert "Поле: quantity" in str(error.value)


def test_arguments_exception_calculate_mass_invalid_source():
    """
    <summary>
    Явно переданная строка вместо единицы отклоняется валидатором.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    flour = item_model("Мука", "Мука пшеничная", group_model("Бакалея"), gram)

    # Действие
    with pytest.raises(arguments_exception) as error:
        flour.calculate_mass(100, gram, "грамм")

    # Проверка
    # pytest.raises проверяет ожидаемый тип исключения.
    assert "Поле: source_unit" in str(error.value)
