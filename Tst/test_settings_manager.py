"""Юнит-тесты менаджера настроек."""
import pytest

from Src.Logics.settings_manager import setting_manager
from Src.Core.validator import operation_exception
from Src.Models.company_model import company_model
from Src.Models.settings_model import settings_model

def test_not_raise_setings_manager_load():
    """
    <summary>
    Загрузка корректного файла настроек завершается без исключений.
    Любое исключение при вызове load приводит к падению теста.
    </summary>
    """
    # Подготовка
    manager = setting_manager()

    # Действие и проверка отсутствия исключений
    manager.load()


def test_not_empty_setings_manager_load():
    """
    <summary>
    После успешной загрузки менеджер предоставляет модель настроек.
    Проверка выполняется после собственной загрузки данных в этом тесте.
    </summary>
    """
    # Подготовка
    manager = setting_manager()

    # Действие
    manager.load()

    # Проверка
    assert isinstance(manager.settings, settings_model)


def test_equals_setings_manager_load():
    """
    <summary>
    Повторное создание менеджера возвращает тот же экземпляр Singleton.
    Проверяется идентичность объектов, а не равенство их значений.
    </summary>
    """
    # Подготовка
    instance1 = setting_manager()

    # Действие
    instance2 = setting_manager()

    # Проверка
    assert instance1 is instance2


def test_is_loaded_settings_manager_true():
    """
    <summary>
    Успешная загрузка устанавливает признак готовности менеджера.
    Состояние проверяется через публичный метод is_loaded.
    </summary>
    """
    # Подготовка
    manager = setting_manager()
    manager._is_loaded = False

    # Действие
    manager.load()

    # Проверка
    assert manager.is_loaded() is True


def test_equals_settings_in_settings_manager():
    """
    <summary>
    Повторное получение Singleton сохраняет ранее загруженные настройки.
    Обе ссылки на менеджер предоставляют тот же объект модели настроек.
    </summary>
    """
    # Подготовка
    instance1 = setting_manager()
    instance1.load()
    loaded_settings = instance1.settings

    # Действие
    instance2 = setting_manager()

    # Проверка
    assert loaded_settings is not None
    assert instance2.settings is loaded_settings


@pytest.fixture
def settings_data():
    """Возвращает новые исходные данные для проверки преобразования."""
    return {
        "company": {
            "name": "Ромашка",
            "inn": "3800000000",
            "bik": "042520000",
            "account": "40702810000000000000",
            "ownership_form": "ООО",
        },
        "boss_name": "Иванов Иван Иванович",
        "account_name": "Петрова Анна Сергеевна",
        "first_start": True,
    }


@pytest.mark.parametrize("first_start", [True, False])
def test_created_settings_convert_valid_data(settings_data, first_start):
    """
    <summary>
    Преобразование создаёт настройки и организацию со всеми реквизитами.
    Оба значения флага первого старта переносятся без изменения.
    </summary>
    """
    # Подготовка
    manager = setting_manager()
    settings_data["first_start"] = first_start
    manager._data = settings_data

    # Действие
    result = manager.convert()

    # Проверка
    assert result is True
    assert isinstance(manager.settings, settings_model)
    assert isinstance(manager.settings.company, company_model)
    for field, expected in settings_data["company"].items():
        assert getattr(manager.settings.company, field) == expected
    assert manager.settings.boss_name == settings_data["boss_name"]
    assert manager.settings.account_name == settings_data["account_name"]
    assert manager.settings.first_start is first_start


@pytest.mark.parametrize("invalid_case", ["missing_first_start", "invalid_first_start"])
def test_operation_exception_convert_invalid_data(settings_data, invalid_case):
    """
    <summary>
    Отсутствующий first_start или строка вместо bool приводят к
    operation_exception с сообщением о неудачном преобразовании.
    Предыдущие корректные настройки сохраняются.
    </summary>
    """
    # Подготовка
    manager = setting_manager()
    manager._data = settings_data
    manager.convert()
    previous_settings = manager.settings
    invalid_data = dict(settings_data)
    if invalid_case == "missing_first_start":
        del invalid_data["first_start"]
    else:
        invalid_data["first_start"] = "false"
    manager._data = invalid_data

    # Действие
    with pytest.raises(operation_exception) as error:
        manager.convert()

    # Проверка
    assert "Не удалось преобразовать настройки" in str(error.value)
    assert manager.settings is previous_settings
