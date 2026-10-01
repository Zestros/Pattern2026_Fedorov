"""Юнит-тесты модели склада."""

import pytest

from Src.Core.abstract_model import abstract_model
from Src.Core.exception import arguments_exception
from Src.Models.warehouse_model import warehouse_model


def test_created_warehouse_model_valid_name():
    """
    <summary>
    Склад создаётся с наименованием без пробелов по краям.
    Модель наследует абстрактную базу и получает уникальный код.
    </summary>
    """
    # Действие
    warehouse = warehouse_model("  Основной склад  ")

    # Проверка
    assert isinstance(warehouse, abstract_model)
    assert warehouse.unique_code != ""
    assert warehouse.name == "Основной склад"


@pytest.mark.parametrize("name", ["", "   ", None, 123, "А" * 51])
def test_arguments_exception_warehouse_model_invalid_name(name):
    """
    <summary>
    Конструктор склада использует общую проверку наименования.
    Пустое, не строковое или слишком длинное имя вызывает
    arguments_exception с указанием поля name.
    </summary>
    """
    # Действие
    with pytest.raises(arguments_exception) as error:
        warehouse_model(name)

    # Проверка
    assert "Поле: name" in str(error.value)


def test_updated_name_warehouse_model_valid_assignment():
    """
    <summary>
    Наименование склада можно изменить после создания.
    Новое значение сохраняется без пробелов по краям.
    </summary>
    """
    # Подготовка
    warehouse = warehouse_model("Основной склад")

    # Действие
    warehouse.name = "  Склад ресторана  "

    # Проверка
    assert warehouse.name == "Склад ресторана"