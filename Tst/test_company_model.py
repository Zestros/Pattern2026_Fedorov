"""Юнит-тесты модели организации."""

import pytest

from Src.Core.abstract_model import abstract_model
from Src.Core.exception import arguments_exception
from Src.Models.company_model import company_model


@pytest.fixture
def company_parameters():
    """Возвращает параметры организации для отдельного теста."""
    return {
        "name": "Ромашка",
        "inn": "0123456789",
        "bik": "012345678",
        "account": "01234567890123456789",
        "ownership_form": "ООО",
    }


def test_created_company_model_valid_parameters(company_parameters):
    """
    <summary>
    Организация сохраняет имя и все реквизиты.
    Ведущие нули в строковых реквизитах сохраняются.
    Модель наследует абстрактную базу и получает уникальный код.
    Значения реквизитов используются как тестовые строки.
    </summary>
    """
    # Действие
    company = company_model(**company_parameters)

    # Проверка
    assert isinstance(company, abstract_model)
    assert company.unique_code != ""

    for field, expected_value in company_parameters.items():
        assert getattr(company, field) == expected_value


def test_trimmed_fields_company_model_surrounding_spaces(
    company_parameters,
):
    """
    <summary>
    При создании организации пробелы по краям имени
    и каждого реквизита удаляются.
    </summary>
    """
    # Подготовка
    parameters = {
        field: f"  {value}  "
        for field, value in company_parameters.items()
    }

    # Действие
    company = company_model(**parameters)

    # Проверка
    for field, expected_value in company_parameters.items():
        assert getattr(company, field) == expected_value


@pytest.mark.parametrize(
    "field",
    ["inn", "bik", "account", "ownership_form"],
)
@pytest.mark.parametrize("value", ["", "   ", None, 123, True])
def test_arguments_exception_company_model_invalid_requisite(
    company_parameters,
    field,
    value,
):
    """
    <summary>
    Пустой или нестроковый реквизит при создании организации
    вызывает arguments_exception с названием соответствующего поля.
    </summary>
    """
    # Подготовка
    company_parameters[field] = value

    # Действие
    with pytest.raises(arguments_exception) as error:
        company_model(**company_parameters)

    # Проверка
    assert f"Поле: {field}" in str(error.value)


def test_arguments_exception_company_model_invalid_name(
    company_parameters,
):
    """
    <summary>
    Конструктор организации использует общую проверку наименования.
    Пустое имя вызывает arguments_exception с полем name.
    </summary>
    """
    # Подготовка
    company_parameters["name"] = ""

    # Действие
    with pytest.raises(arguments_exception) as error:
        company_model(**company_parameters)

    # Проверка
    assert "Поле: name" in str(error.value)


@pytest.mark.parametrize(
    "field, value, expected_value",
    [
        ("inn", "  0012345678  ", "0012345678"),
        ("bik", "  001234567  ", "001234567"),
        ("account", "  00123456789012345678  ", "00123456789012345678"),
        ("ownership_form", "  АО  ", "АО"),
    ],
)
def test_updated_requisite_company_model_valid_assignment(
    company_parameters,
    field,
    value,
    expected_value,
):
    """
    <summary>
    Реквизит организации можно изменить после создания.
    Новое значение сохраняется без пробелов по краям.
    </summary>
    """
    # Подготовка
    company = company_model(**company_parameters)

    # Действие
    setattr(company, field, value)

    # Проверка
    assert getattr(company, field) == expected_value


@pytest.mark.parametrize(
    "field",
    ["inn", "bik", "account", "ownership_form"],
)
@pytest.mark.parametrize("value", ["", "   ", None, 123, True])
def test_unchanged_requisite_company_model_invalid_assignment(
    company_parameters,
    field,
    value,
):
    """
    <summary>
    Недопустимое новое значение реквизита вызывает arguments_exception.
    Исключение содержит название поля, прежнее значение сохраняется.
    </summary>
    """
    # Подготовка
    company = company_model(**company_parameters)
    previous_value = getattr(company, field)

    # Действие
    with pytest.raises(arguments_exception) as error:
        setattr(company, field, value)

    # Проверка
    assert f"Поле: {field}" in str(error.value)
    assert getattr(company, field) == previous_value