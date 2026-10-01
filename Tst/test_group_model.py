"""Тесты для модели групп номекнлатуры"""

import pytest

from Src.Core.abstract_model import abstract_model
from Src.Core.exception import arguments_exception
from Src.Models.group_model import group_model


@pytest.mark.parametrize(
    "name, expected_name",
    [
        ("Продукты", "Продукты"),
        ("  Молочные продукты  ", "Молочные продукты"),
        ("А", "А"),
        ("А" * 50, "А" * 50),
    ],
)
def test_created_group_model_valid_name(name, expected_name):
    """
    <summary>
    Группа создаётся с допустимым наименованием.
    Пробелы по краям удаляются; длина 1 и 50 символов допустима.
    Модель наследуется от abstract_model и получает уникальный код.
    </summary>
    """
    # Подготовка и действие
    group = group_model(name)

    # Проверка
    assert isinstance(group, abstract_model)
    assert group.name == expected_name
    assert group.unique_code != ""



@pytest.mark.parametrize(
    "name",
    ["", "   ", "А" * 51, None, 123],
)
def test_arguments_exception_group_model_invalid_name(name):
    """
    <summary>
    Создание группы с пустым, слишком длинным или нестроковым
    наименованием вызывает внутреннее исключение проекта.
    </summary>
    """
    # Действие
    with pytest.raises(arguments_exception) as error:
        group_model(name)

    # Проверка
    assert "Поле: name" in str(error.value)



def test_updated_name_group_model_valid_name_assignment():
    """
    <summary>
    После создания группы её наименование можно изменить.
    Новое значение сохраняется без пробелов по краям.
    </summary>
    """
    # Подготовка
    group = group_model("Продукты")

    # Действие
    group.name = "  Напитки  "

    # Проверка
    assert group.name == "Напитки"


@pytest.mark.parametrize(
    "name",
    ["", "   ", "А" * 51, None, 123],
)
def test_unchanged_name_group_model_invalid_name_assignment(name):
    """
    <summary>
    Недопустимое новое наименование вызывает arguments_exception.
    Ранее установленное наименование группы сохраняется.
    </summary>
    """
    # Подготовка
    group = group_model("Продукты")

    # Действие
    with pytest.raises(arguments_exception):
        group.name = name

    # Проверка
    assert group.name == "Продукты"