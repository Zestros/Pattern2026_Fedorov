"""Проверки сервиса отчётов без HTTP и общего результата."""
import pytest

from Src.Models.unit_model import unit_model
from Src.Models.item_model import item_model
from Src.Core.report_type_enum import report_type_enum
from Src.Dtos.report_data_dto import report_data_dto
from Src.Logics.report_factory import report_factory
from Src.Logics.report_source_factory import report_source_factory
from Src.Logics.report_service import report_service, report_not_found_exception
from Src.Logics.storage_manager import storage_manager
from Src.Models.settings_model import settings_model


@pytest.mark.parametrize("format_", list(report_type_enum))
def test_correct_result_service_explicit_and_default(monkeypatch, format_):
    """<summary>Сервис использует код сущности и выбранный способ определения формата.</summary>"""
    # Подготовка
    monkeypatch.setattr(storage_manager, "_storage_manager__instance", None)
    settings = settings_model()
    settings.response_format = format_
    storage = storage_manager(settings)
    unit = storage.units[0]
    service = report_service(storage, report_source_factory(), report_factory(settings))
    # Действие
    explicit = service.build(unit_model, unit.unique_code, format_)
    default = service.build_default(unit_model, unit.unique_code)
    # Проверка
    assert explicit == default
    content = explicit.content.decode() if isinstance(explicit.content, bytes) else explicit.content
    assert unit.unique_code in content
    assert unit.name in content


def test_not_found_service_missing_entity(monkeypatch):
    """<summary>Отсутствие сущности сообщается предметным исключением без HTTP-ответа.</summary>"""
    # Подготовка
    monkeypatch.setattr(storage_manager, "_storage_manager__instance", None)
    settings = settings_model()
    service = report_service(storage_manager(settings), report_source_factory(), report_factory(settings))
    # Действие и Проверка
    with pytest.raises(report_not_found_exception):
        service.build_default(item_model, "missing")


@pytest.mark.parametrize("format_", list(report_type_enum))
def test_empty_value_build_none(format_):
    """<summary>Отсутствующее значение не выводится служебным словом None.</summary>"""
    # Подготовка
    data = report_data_dto("", (("Поле", None),), ("Значение",), ((None,),))
    # Действие
    result = report_factory(settings_model()).create(format_).build(data)
    # Проверка
    content = result.content.decode() if isinstance(result.content, bytes) else result.content
    assert "None" not in content
    assert "Поле" in content
