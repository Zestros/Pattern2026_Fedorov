"""Юнит-тесты проверки числовых значений"""

import pytest

from Src.Core.exception import arguments_exception
from Src.Core.validator import validator


@pytest.mark.parametrize("value", [0, 1, 0.5])
def test_accepted_number_validate_number_valid_value(value):
    """
    <summary>
    Неотрицательные целые и дробные числа проходят проверку.
    </summary>
    """
    assert validator.validate_number(value, "quantity") is True


@pytest.mark.parametrize(
    "value",
    [
        -1,
        -0.5,
        True,
        False,
        "100",
        None,
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_arguments_exception_validate_number_invalid_value(value):
    """
    <summary>
    Отрицательные, нечисловые и неконечные значения отклоняются.
    Исключение содержит название проверяемого поля.
    </summary>
    """
    with pytest.raises(arguments_exception) as error:
        validator.validate_number(value, "quantity")

    assert "Поле: quantity" in str(error.value)


def test_arguments_exception_validate_number_zero_forbidden():
    """
    <summary>
    Ноль отклоняется, когда требуется строго положительное число.
    </summary>
    """
    with pytest.raises(arguments_exception) as error:
        validator.validate_number(0, "density", allow_zero=False)

    assert "Поле: density" in str(error.value)


def test_accepted_number_validate_number_positive_value():
    """
    <summary>
    Положительная дробь проходит проверку при запрете нуля.
    </summary>
    """
    assert validator.validate_number(
        0.9, "density", allow_zero=False
    ) is True