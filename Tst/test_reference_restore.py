"""Проверки восстановления типов, ссылок и отклонения некорректного графа."""

import json
from datetime import datetime, timedelta, timezone

import pytest

from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Core.report_type_enum import report_type_enum
from Src.Logics.convert_factory import convert_factory
from Src.Logics.reference_restore import reference_restore
from Src.Models.company_model import company_model
from Src.Models.group_model import group_model
from Src.Models.recipe_model import recipe_model
from Src.Models.settings_model import settings_model
from Src.Models.unit_model import unit_model
from Src.Models.warehouse_model import warehouse_model


@pytest.mark.parametrize("source", [None, True, False, 0, -12, 1.5, "", "Мука"])
def test_preserved_type_reference_restore_restore_basic_value(source):
    """<summary>Простые значения восстанавливаются без изменения точного Python-типа.</summary>"""
    # Подготовка
    data = convert_factory().create(source).convert(source)
    # Действие
    restored = reference_restore().restore(json.loads(json.dumps(data)))
    # Проверка
    assert type(restored) is type(source)
    assert restored == source


def test_restored_datetime_reference_restore_restore_fold_and_literal_string():
    """<summary>Метка даты сохраняет fold, смещение и тип, не меняя обычную ISO-строку.</summary>"""
    # Подготовка
    date = datetime(2026, 10, 22, 18, 30, tzinfo=timezone(timedelta(hours=8)), fold=1)
    source = [date, date.isoformat()]
    data = convert_factory().create(source).convert(source)
    # Действие
    restored = reference_restore().restore(json.loads(json.dumps(data)))
    # Проверка
    assert restored[0] == date
    assert restored[0].fold == 1
    assert restored[0].utcoffset() == timedelta(hours=8)
    assert type(restored[1]) is str


@pytest.mark.parametrize("model_type", [group_model, warehouse_model])
def test_restored_model_reference_restore_restore_named_model(model_type):
    """<summary>Группа и склад восстанавливаются в исходный класс с сохранённым кодом.</summary>"""
    # Подготовка
    source = model_type("Пример")
    data = convert_factory().create(source).convert(source)
    # Действие
    restored = reference_restore().restore(data)
    # Проверка
    assert type(restored) is model_type
    assert restored is not source
    assert restored.name == source.name
    assert restored.unique_code == source.unique_code


def test_restored_settings_reference_restore_restore_company_and_enum():
    """<summary>Настройки сохраняют организацию, её реквизиты и тип перечисления формата.</summary>"""
    # Подготовка
    source = settings_model()
    source.company = company_model("Ромашка", "123", "456", "789", "ООО")
    source.boss_name = "Директор"
    source.account_name = "Бухгалтер"
    source.response_format = report_type_enum.XML
    data = convert_factory().create(source).convert(source)
    # Действие
    restored = reference_restore().restore(json.loads(json.dumps(data)))
    # Проверка
    assert restored.company.unique_code == source.company.unique_code
    assert restored.company.inn == "123"
    assert restored.company.bik == "456"
    assert restored.company.account == "789"
    assert restored.company.ownership_form == "ООО"
    assert restored.response_format is source.response_format
    assert restored.boss_name == "Директор"
    assert restored.account_name == "Бухгалтер"


def test_restored_defaults_reference_restore_restore_empty_settings():
    """<summary>Необязательная организация и пустые начальные имена остаются значениями по умолчанию.</summary>"""
    # Подготовка
    source = settings_model()
    data = convert_factory().create(source).convert(source)
    # Действие
    restored = reference_restore().restore(data)
    # Проверка
    assert restored.company is None
    assert restored.boss_name == restored.account_name == ""
    assert restored.response_format is report_type_enum.TXT
    assert restored.unique_code == source.unique_code


def test_restored_entity_reference_restore_restore_public_self_reference():
    """<summary>Базовая именованная модель сохраняет публичное поле с обратной ссылкой.</summary>"""
    # Подготовка
    source = entity_model()
    source.name = "Узел"
    source.link = source
    data = convert_factory().create(source).convert(source)
    # Действие
    restored = reference_restore().restore(data)
    # Проверка
    assert restored.name == "Узел"
    assert restored.link is restored
    assert restored.unique_code == source.unique_code


def test_forward_reference_reference_restore_restore_definition_after_reference():
    """<summary>Предварительная индексация позволяет ссылаться на определение позднее в документе.</summary>"""
    # Подготовка
    data = {"value": {"$id": "1", "$type": "list", "$values": [
        {"$ref": "2"}, {"$id": "2", "$type": "list", "$values": [1]},
    ]}}
    # Действие
    restored = reference_restore().restore(data)
    # Проверка
    assert restored == [[1], [1]]
    assert restored[0] is restored[1]


@pytest.mark.parametrize("value, message", [
    ({"$ref": "missing"}, "Неизвестная ссылка"),
    ({"$ref": "1", "name": "unexpected"}, "только строковый $ref"),
    ({"$type": "os.system", "$id": "1", "$fields": {}}, "Неизвестный тип"),
    ({"$id": "1", "$type": "list", "$values": [
        {"$id": "1", "$type": "list", "$values": []},
    ]}, "Повторное определение"),
    ({"$id": "1", "$type": "dict", "$items": [[1, 2], [1, 3]]}, "Повторный ключ"),
    ({"$id": "1", "$type": "dict", "$items": [[1]]}, "пары ключ-значение"),
    ({"$id": "1", "$type": "list", "$values": {}}, "Ожидается массив"),
    ({"$type": "datetime", "$value": "bad date", "$fold": 0}, "Некорректные данные"),
    ({"$type": "datetime", "$value": "2026-10-22", "$fold": 3}, "$fold"),
    ({"$id": "1", "$type": "SimpleNamespace", "$fields": {"_private": 1}}, "публичные"),
    ({"$id": "1", "$type": "tuple", "$values": [{"$ref": "1"}]}, "tuple"),
])
def test_arguments_exception_reference_restore_restore_invalid_graph(value, message):
    """<summary>Неверные ссылки, типы и формы графа отклоняются с понятной причиной.</summary>"""
    # Подготовка
    reader = reference_restore()
    data = {"value": value}
    # Действие
    with pytest.raises(arguments_exception) as error:
        reader.restore(data)
    # Проверка
    assert message in str(error.value)


def test_domain_validation_reference_restore_restore_invalid_unit():
    """<summary>Восстановление использует проверку конструктора единицы и отклоняет нулевой коэффициент.</summary>"""
    # Подготовка
    source = unit_model("грамм")
    data = convert_factory().create(source).convert(source)
    data["value"]["$fields"]["coefficient"] = 0
    # Действие
    with pytest.raises(arguments_exception) as error:
        reference_restore().restore(data)
    # Проверка
    assert "Коэффициент должен быть больше нуля" in str(error.value)


def test_computed_validation_reference_restore_restore_changed_recipe_total():
    """<summary>Расчётная масса не присваивается из JSON; несовпадение с пересчётом отклоняется.</summary>"""
    # Подготовка
    source = recipe_model("Пустая карта", unit_model("грамм"))
    data = convert_factory().create(source).convert(source)
    data["value"]["$fields"]["net_weight"] = 100
    # Действие
    with pytest.raises(arguments_exception) as error:
        reference_restore().restore(data)
    # Проверка
    assert "Расчётное поле" in str(error.value)


def test_independent_graphs_reference_restore_restore_repeated_calls():
    """<summary>Повторные вызовы одного восстановителя создают независимые графы с теми же кодами.</summary>"""
    # Подготовка
    source = unit_model("грамм")
    data = convert_factory().create(source).convert(source)
    reader = reference_restore()
    # Действие
    first = reader.restore(data)
    second = reader.restore(data)
    # Проверка
    assert first is not second
    assert first.base_unit is first
    assert second.base_unit is second
    assert first.unique_code == second.unique_code == source.unique_code
