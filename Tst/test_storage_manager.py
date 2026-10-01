"""Юнит-тесты менеджера хранения."""
import pytest

from Src.Logics.storage_manager import storage_manager
from Src.Models.settings_model import settings_model

def test_same_instance_storage_manager_repeated_creation(settings):
    """
    <summary>
    Повторное создание менеджера возвращает тот же экземпляр.
    Ранее созданная номенклатура сохраняется без повторной генерации.
    </summary>
    """
    # Подготовка
    settings.first_start = True
    first = storage_manager(settings)
    item = first.items[0]

    # Действие
    second = storage_manager(settings)

    # Проверка
    assert first is second
    assert second.items[0] is item


def test_filled_collections_storage_manager_first_start(settings):
    """
    <summary>
    При включённом первом старте менеджер создаёт примерные группы,
    склады, номенклатуру и единицы измерения.
    После инициализации менеджер сообщает об успешной загрузке.
    </summary>
    """
    # Подготовка
    settings.first_start = True

    # Действие
    manager = storage_manager(settings)

    # Проверка
    assert manager.is_loaded()
    assert manager.groups
    assert manager.warehouses
    assert manager.items
    assert manager.units


def test_empty_collections_storage_manager_regular_start(settings):
    """
    <summary>
    При выключенном первом старте менеджер не создаёт примерные данные.
    Все коллекции остаются пустыми, инициализация завершается успешно.
    </summary>
    """
    # Подготовка
    settings.first_start = False

    # Действие
    manager = storage_manager(settings)

    # Проверка
    assert manager.is_loaded()
    assert not manager.groups
    assert not manager.warehouses
    assert not manager.items
    assert not manager.units