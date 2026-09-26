"""Юнит-тесты базовых моделей и проверки аргументов."""
from Src.Core.abstract_model import abstract_model
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


@pytest.mark.parametrize("other", [None, "код", 123, object()])
def test_not_implemented_abstract_model_eq_unsupported_type(other):
    """
    <summary>
    Метод сравнения возвращает NotImplemented для постороннего типа.
    Обычное сравнение с указанными объектами даёт False без исключения.
    </summary>
    """
    # Подготовка
    entity = test_entity()

    # Действие
    method_result = entity.__eq__(other)
    comparison_result = entity == other

    # Проверка
    assert method_result is NotImplemented
    assert comparison_result is False

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

def test_trimmed_code_abstract_model_unique_code_assignment():
    """
    <summary>
    При присваивании уникального кода пробелы по краям удаляются.
    </summary>
    """
    # Подготовка
    entity = test_entity()

    # Действие
    entity.unique_code = "  product-001  "

    # Проверка
    assert entity.unique_code == "product-001"

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
    <summary>Не строковый код вызывает arguments_exception с полем unique_code и причиной ошибки.</summary>
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



