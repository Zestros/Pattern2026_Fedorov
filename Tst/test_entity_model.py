"""Юнит-тесты базовых моделей и проверки аргументов."""
from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
import pytest


def test_not_value_error_entity_model_name_when_empty_value_set():
    """
    <summary>Пустое имя вызывает arguments_exception, не являющееся ValueError.</summary>
    """
    # Подготовка
    entity = entity_model()

    # Действие
    with pytest.raises(arguments_exception) as exception:
        entity.name = ""

    # Проверка
    assert not isinstance(exception.value, ValueError)

def test_arguments_exception_with_details_entity_model_name_when_empty_value_set():
    """
    <summary>Пустое имя вызывает arguments_exception с полем name и причиной ошибки.</summary>
    """
    # Подготовка
    entity = entity_model()
    name = ""

    # Действие
    with pytest.raises(arguments_exception) as exception:
        entity.name = name

    # Проверка
    assert "Поле: name" in str(exception.value)
    assert "Наименование не может быть пустым" in str(exception.value)

def test_arguments_exception_with_details_entity_model_name_when_name_is_not_string():
    """
    <summary>Не строковое имя вызывает arguments_exception с полем name и причиной ошибки.</summary>
    """
    # Подготовка
    entity = entity_model()
    name = 42

    # Действие
    with pytest.raises(arguments_exception) as exception:
        entity.name = name

    # Проверка
    assert "Поле: name" in str(exception.value)
    assert "Наименование должно быть строкой" in str(exception.value)
