"""Тесты создания отчётов через фабрику."""

import pytest
from Src.Core.exception import arguments_exception
from Src.Core.report_type_enum import report_type_enum
from Src.Logics.report_factory import report_factory
from Src.Logics.text_report import text_report
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
    report = report_factory()
    
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
    report = report_factory()
    
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
    factory = report_factory()
    cake = recipe_item_model.create_cake(
        group_model.create_grocery(),
        unit_model("грамм"),
        unit_model.create_piece(),
    )
    layers, cream = cake.recipe.ingredients
    report = factory.create(report_type_enum.TXT)

    # Действие
    result = report.build(cake.recipe)

    # Проверка
    assert result.text.splitlines() == [
        "Код | Наименование | Брутто | Нетто",
        f"{layers.unique_code} | Бисквитный корж | 405.0 | 405.0",
        f"{cream.unique_code} | Порция крема | 400.0 | 400.0",
    ]