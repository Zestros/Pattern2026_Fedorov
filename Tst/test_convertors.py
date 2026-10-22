"""Модульные тесты контракта конверторов и чтения полей моделей."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from Src.Core.abstract_convertor import abstract_convertor
from Src.Dtos.conversion_context_dto import conversion_context_dto
from Src.Core.exception import arguments_exception
from Src.Logics.basic_convertor import basic_convertor
from Src.Logics.convert_factory import convert_factory
from Src.Logics.datetime_convertor import datetime_convertor
from Src.Logics.reference_convertor import reference_convertor
from Src.Models.group_model import group_model


def test_type_error_abstract_convertor_when_instantiated():
    """<summary>Базовый конвертор нельзя создать без реализации контракта.</summary>"""
    # Подготовка
    convertor_type = abstract_convertor

    # Действие
    with pytest.raises(TypeError) as error:
        convertor_type()

    # Проверка
    assert "convert" in str(error.value)


@pytest.mark.parametrize("value", [0, -12, 1.25, "", "Мука", True, False, None])
def test_preserved_value_basic_convertor_convert_simple_types(value):
    """<summary>Простые значения сохраняют содержимое, имя поля и точный тип.</summary>"""
    # Подготовка
    convertor = basic_convertor()

    # Действие
    result = convertor.convert(value, "field")

    # Проверка
    assert result == {"field": value}
    assert type(result["field"]) is type(value)


@pytest.mark.parametrize("value", [[], {}, datetime(2026, 10, 22)])
def test_arguments_exception_basic_convertor_convert_unsupported_type(value):
    """<summary>Прямой вызов простого конвертора отклоняет составные значения и дату.</summary>"""
    # Подготовка
    convertor = basic_convertor()

    # Действие
    with pytest.raises(arguments_exception) as error:
        convertor.convert(value, "field")

    # Проверка
    assert "Поле: field" in str(error.value)


@pytest.mark.parametrize("value, expected", [
    (datetime(2026, 10, 22, 18, 30), "2026-10-22T18:30:00"),
    (
        datetime(2026, 10, 22, 18, 30, 15, 123456,
                 tzinfo=timezone(timedelta(hours=8))),
        "2026-10-22T18:30:15.123456+08:00",
    ),
])
def test_iso_string_datetime_convertor_convert_date_and_timezone(value, expected):
    """<summary>Дата сохраняет время, микросекунды и смещение без добавления пояса.</summary>"""
    # Подготовка
    convertor = datetime_convertor()

    # Действие
    result = convertor.convert(value, "created_at")

    # Проверка
    assert result == {
        "created_at": expected,
    }


def test_arguments_exception_datetime_convertor_convert_string():
    """<summary>Конвертор даты отклоняет строку вместо неявного разбора её содержимого.</summary>"""
    # Подготовка
    convertor = datetime_convertor()
    source = "2026-10-22"

    # Действие
    with pytest.raises(arguments_exception) as error:
        convertor.convert(source)

    # Проверка
    assert "Тип str не поддерживается конвертором" in str(error.value)


def test_inherited_fields_reference_convertor_convert_group():
    """<summary>Свойства базовых классов группы раскрываются под публичными именами.</summary>"""
    # Подготовка
    group = group_model("Бакалея")
    convertor = reference_convertor(convert_factory())

    # Действие
    result = convertor.convert(group, "group")

    # Проверка
    assert result == {
        "group": {"name": "Бакалея", "unique_code": group.unique_code},
    }


def test_public_fields_reference_convertor_convert_instance_attributes():
    """<summary>Обычные атрибуты экземпляра читаются, приватные поля и функции исключаются.</summary>"""
    # Подготовка
    source = SimpleNamespace(name="Мука", quantity=2, _secret="hidden", run=lambda: 1)
    factory = convert_factory()

    # Действие
    result = factory.convert(source)

    # Проверка
    assert result == {
        "value": {"name": "Мука", "quantity": 2},
    }


def test_no_getter_calls_reference_convertor_get_fields_before_conversion():
    """<summary>Поиск имён свойств не вызывает getter и не изменяет счётчик чтений.</summary>"""
    # Подготовка
    class counted_source:
        """Тестовый объект со счётчиком чтений свойства."""

        def __init__(self):
            """Создаёт приватный счётчик обращений."""
            self._reads = 0

        @property
        def quantity(self):
            """Увеличивает счётчик и возвращает количество."""
            self._reads += 1
            return 3

    source = counted_source()

    # Действие
    fields = reference_convertor._get_fields(source)

    # Проверка
    assert fields == ["quantity"]
    assert source._reads == 0


def test_clean_context_reference_convertor_convert_when_getter_fails():
    """<summary>Ошибка getter не скрывается; активные объекты и путь очищаются.</summary>"""
    # Подготовка
    class failing_source:
        """Тестовый объект с временно недоступным свойством."""

        def __init__(self):
            """Включает ошибку чтения."""
            self._fail = True

        @property
        def quantity(self):
            """Возвращает количество после устранения ошибки."""
            if self._fail:
                raise RuntimeError("Ошибка чтения")
            return 3

    source = failing_source()
    context = conversion_context_dto()
    factory = convert_factory()

    # Действие
    with pytest.raises(RuntimeError, match="Ошибка чтения"):
        factory.convert(source, context=context)

    # Проверка
    assert context.active_ids == set()
    assert context.path == []



@pytest.mark.parametrize("convertor_type, source", [
    (basic_convertor, 1),
    (datetime_convertor, datetime(2026, 10, 22)),
    (reference_convertor, []),
])
def test_arguments_exception_abstract_convertor_convert_non_string_field(convertor_type, source):
    """<summary>Общая проверка отвергает нестроковое имя поля у всех конверторов.</summary>"""
    # Подготовка
    convertor = convertor_type(convert_factory())

    # Действие
    with pytest.raises(arguments_exception) as error:
        convertor.convert(source, 42)

    # Проверка
    assert "Поле: field_name" in str(error.value)
