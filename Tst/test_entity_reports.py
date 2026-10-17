"""Модульные проверки подготовки отчётов и поиска сущностей."""
from Src.Core.entity_type_enum import entity_type_enum
from Src.Logics.report_source_factory import report_source_factory

import pytest

from Src.Core.exception import arguments_exception
from Src.Core.report_type_enum import report_type_enum
from Src.Logics.report_factory import report_factory
from Src.Logics.storage_manager import storage_manager
from Src.Models.settings_model import settings_model
from Src.Models.recipe_item_model import recipe_item_model


@pytest.fixture
def storage(monkeypatch):
    """Создаёт изолированное хранилище с первичными данными."""
    monkeypatch.setattr(storage_manager, "_storage_manager__instance", None)
    return storage_manager(settings_model())


def contracts():
    """Возвращает типы сущностей и новую фабрику обработчиков."""
    return entity_type_enum, report_source_factory()


@pytest.mark.parametrize("kind", ["ITEM", "UNIT", "RECIPE"])
def test_correct_fields_build_entity(storage, kind):
    """<summary>Обработчик сохраняет идентичность и предметные поля выбранной сущности.</summary>"""
    # Подготовка
    types, factory = contracts()
    product = next(item for item in storage.items if isinstance(item, recipe_item_model))
    entity = {"ITEM": storage.items[0], "UNIT": storage.units[1], "RECIPE": product.recipe}[kind]
    # Действие
    data = factory.create(types[kind]).build(entity)
    fields = dict(data.fields)
    # Проверка
    assert fields["Код"] == entity.unique_code
    assert fields["Наименование"] == entity.name
    if kind == "ITEM":
        assert fields["Полное наименование"] == entity.full_name
        assert fields["Код группы"] == entity.group.unique_code
        assert fields["Единица измерения"] == entity.unit.name
        assert data.rows == ()
    elif kind == "UNIT":
        assert fields["Коэффициент"] == entity.coefficient
        assert fields["Код базовой единицы"] == entity.base_unit.unique_code
        assert data.rows == ()
    else:
        assert fields["Единица массы"] == entity.mass_unit.name
        assert fields["Брутто"] == pytest.approx(498.5)
        assert fields["Нетто"] == pytest.approx(498.5)
        assert len(data.rows) == 4
        assert [row[1] for row in data.rows] == ["Мука", "Вода", "Масло", "Соль"]


@pytest.mark.parametrize("kind", ["ITEM", "UNIT", "RECIPE"])
@pytest.mark.parametrize("format_", list(report_type_enum))
def test_preserved_identity_build_all_entity_formats(storage, kind, format_):
    """<summary>Все 15 сочетаний типа и формата содержат код и название объекта.</summary>"""
    # Подготовка
    types, factory = contracts()
    product = next(item for item in storage.items if isinstance(item, recipe_item_model))
    entity = {"ITEM": storage.items[0], "UNIT": storage.units[0], "RECIPE": product.recipe}[kind]
    # Действие
    result = report_factory(settings_model()).create(format_).build(factory.create(types[kind]).build(entity))
    text = result.content.decode() if result.download else result.content
    # Проверка
    assert entity.unique_code in text
    assert entity.name in text


@pytest.mark.parametrize("kind", ["ITEM", "UNIT", "RECIPE"])
def test_found_entity_find_own_code(storage, kind):
    """<summary>Поиск возвращает исходный объект, для рецепта используется код карты.</summary>"""
    # Подготовка
    types, _ = contracts()
    product = next(item for item in storage.items if isinstance(item, recipe_item_model))
    entity = {"ITEM": product, "UNIT": storage.units[0], "RECIPE": product.recipe}[kind]
    # Действие и Проверка
    assert storage.find(types[kind], entity.unique_code) is entity
    assert storage.find(types[kind], "unknown") is None
    assert storage.find(types.RECIPE, product.unique_code) is None


@pytest.mark.parametrize("kind", ["ITEM", "UNIT", "RECIPE"])
def test_rejected_source_build_wrong_model(storage, kind):
    """<summary>Обработчики отклоняют объекты, не соответствующие их контракту.</summary>"""
    # Подготовка
    types, factory = contracts()
    # Действие и Проверка
    with pytest.raises(arguments_exception):
        factory.create(types[kind]).build(object())


def test_rejected_arguments_factory_and_find(storage):
    """<summary>Неизвестный тип и пустой код отклоняются явно.</summary>"""
    # Подготовка
    types, factory = contracts()
    # Действие и Проверка
    with pytest.raises(arguments_exception):
        factory.create("item")
    with pytest.raises(arguments_exception):
        storage.find("item", "code")
    with pytest.raises(arguments_exception):
        storage.find(types.ITEM, " ")
