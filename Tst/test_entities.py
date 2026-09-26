"""Юнит-тесты базовых моделей и проверки аргументов."""
from Src.Core.abstract_model import abstract_model
from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
import pytest

class test_entity(abstract_model):
    """Модель для проверки поведения abstract_model."""

    pass

def test_not_empty_abstract_model_unique_code_after_creation():
    """
    <summary>После создания модели её уникальный код не пустой.</summary>
    """

    # Подготовка
    entity = test_entity()

    # Действие
    result = entity.unique_code

    # Проверка
    assert result != ""

def test_different_codes_abstract_model_unique_code_for_two_entities():
    """
    <summary>Две созданные модели получают разные уникальные коды.</summary>
    """

    # Подготовка
    entity_1 = test_entity()
    entity_2 = test_entity()

    # Действие
    id_1 = entity_1.unique_code
    id_2 = entity_2.unique_code

    # Проверка
    assert id_1 != id_2

def test_equal_entities_abstract_model_eq_when_codes_match():
    """
    <summary>После ручного присвоения одинаковых кодов две модели равны.</summary>
    """

    # Подготовка
    entity_1 = test_entity()
    entity_2 = test_entity()

    # Действие
    entity_1.unique_code = "fff"
    entity_2.unique_code = "fff"

    # Проверка
    assert entity_1 == entity_2

def test_arguments_exception_with_details_entity_unique_code_when_code_is_not_string():
    """
    <summary>Не строковый код вызывает arguments_exception с полем name и причиной ошибки.</summary>
    """

    # Подготовка
    entity = test_entity()
    code = None

    # Действие
    with pytest.raises(arguments_exception) as exception:
        entity.unique_code = code

    # Проверка
    assert "Поле: unique_code" in str(exception.value)
    assert "Уникальный код должен быть строкой" in str(exception.value)

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
