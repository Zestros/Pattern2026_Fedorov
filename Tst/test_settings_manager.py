from Src.Logics.settings_manager import setting_manager
from Src.Core.validator import validator, operation_exception


def test_not_raise_setings_manager_load():
    # Подготовка
    manager = setting_manager()
    # Действие и проверка
    try:
        manager.load()
        assert True
    except operation_exception:
        assert False
    except: False

"""
Проверить загрузку настроек. Настройки не пустые
"""
def test_not_empty_setings_manager_load():
    # Подготовка
    manager = setting_manager()

    # Действие и проверка
    try:
        manager.load()
    except:
        assert True

    assert manager.settings is not None


def test_equals_setings_manager_load():
    # Подготовка
    instance1 = setting_manager()
    instance2 = setting_manager()

    # Действие

    # Проверка
    assert instance1 == instance2

def test_is_loaded_settings_manager_true():
    # Подготовка
    manager = setting_manager()

    # Действие и проверка
    try:
        manager.load()
    except:
        assert False
    assert manager._is_loaded

def test_equals_settings_in_settings_manager():
    # Подготовка
    instance1 = setting_manager()
    instance2 = setting_manager()

    # Действие

    # Проверка
    assert instance1.settings == instance2.settings