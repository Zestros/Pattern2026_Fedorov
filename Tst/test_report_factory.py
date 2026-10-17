"""Тесты создания отчётов через фабрику."""

import pytest
from Src.Models.settings_model import settings_model
from Src.Core.exception import arguments_exception
from Src.Core.report_type_enum import report_type_enum
from Src.Logics.report_factory import report_factory
from Src.Logics.text_report import text_report
from Src.Logics.recipe_report_source import recipe_report_source
from Src.Models.group_model import group_model
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.unit_model import unit_model


def test_created_text_report_create_supported_type():
    """
    <summary>
    Для поддерживаемого типа фабрика возвращает
    экземпляр текстового отчёта.
    </summary>
    """
    # Подготовка
    report = report_factory(settings_model())
    
    # Действие
    report = report.create(report_type_enum.TXT)

    # Проверка
    assert isinstance(report, text_report)

def test_created_text_report_create_unsupported_type():
    """
    <summary>
    Для не поддерживаемого типа фабрика возвращает
    экземпляр текстового отчёта.
    </summary>
    """
    # Подготовка
    report = report_factory(settings_model())
    
    # Действие
    with pytest.raises(arguments_exception) as error:
        report.create(999)

    # Проверка
    assert "Поле: report_type" in str(error.value)



def test_correct_text_build_report_created_by_factory():
    """
    <summary>
    Созданный фабрикой отчёт формирует заголовок и обе строки
    торта с правильными кодами, названиями и массами.
    </summary>
    """
    # Подготовка
    factory = report_factory(settings_model())
    cake = recipe_item_model.create_cake(
        group_model.create_grocery(),
        unit_model("грамм"),
        unit_model.create_piece(),
    )
    layers, cream = cake.recipe.ingredients
    report = factory.create(report_type_enum.TXT)

    # Действие
    result = report.build(recipe_report_source().build(cake.recipe))

    # Проверка
    assert result.content.splitlines() == [
        cake.recipe.name,
        f"Код: {cake.recipe.unique_code}",
        f"Наименование: {cake.recipe.name}",
        f"Код единицы массы: {cake.recipe.mass_unit.unique_code}",
        f"Единица массы: {cake.recipe.mass_unit.name}",
        "Брутто: 805.0",
        "Нетто: 805.0",
        "Код строки | Наименование | Код номенклатуры | Количество | Брутто | Нетто",
        f"{layers.unique_code} | Бисквитный корж | {layers.item.unique_code} | {layers.quantity} | 405.0 | 405.0",
        f"{cream.unique_code} | Порция крема | {cream.item.unique_code} | {cream.quantity} | 400.0 | 400.0",
    ]