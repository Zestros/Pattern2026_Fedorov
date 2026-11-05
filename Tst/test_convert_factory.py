"""Модульные проверки выбора конвертора и сохранения графа объектов."""

import json
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from Src.Core.abstract_convertor import abstract_convertor
from Src.Core.abstract_model import abstract_model
from Src.Dtos.conversion_context_dto import conversion_context_dto
from Src.Core.exception import arguments_exception
from Src.Logics.basic_convertor import basic_convertor
from Src.Logics.convert_factory import convert_factory
from Src.Logics.datetime_convertor import datetime_convertor
from Src.Logics.reference_convertor import reference_convertor
from Src.Logics.reference_restore import reference_restore
from Src.Models.group_model import group_model
from Src.Models.unit_model import unit_model


@pytest.mark.parametrize("source, expected_type", [
    (1, basic_convertor), ("Мука", basic_convertor), (None, basic_convertor),
    (datetime(2026, 10, 22), datetime_convertor),
    ([], reference_convertor), ({}, reference_convertor),
    ((), reference_convertor), (group_model("Бакалея"), reference_convertor),
])
def test_selected_convertor_convert_factory_create_supported_type(source, expected_type):
    """<summary>Фабрика возвращает реализацию общего контракта по типу значения.</summary>"""
    # Подготовка
    factory = convert_factory()
    # Действие
    result = factory.create(source)
    # Проверка
    assert isinstance(result, abstract_convertor)
    assert isinstance(result, expected_type)


def test_not_read_properties_convert_factory_create_model():
    """<summary>Выбор конвертора не запускает getter и не преобразует модель.</summary>"""
    # Подготовка
    class source_model:
        """Объект с недоступным значением свойства."""

        @property
        def quantity(self):
            """Отклоняет преждевременное чтение."""
            raise RuntimeError("Значение должен читать конвертор")

    factory = convert_factory()
    source = source_model()
    # Действие
    result = factory.create(source)
    # Проверка
    assert isinstance(result, reference_convertor)


def test_self_reference_reference_convertor_convert_base_unit():
    """<summary>Грамм хранится полностью, а его база ссылается на его служебный ID.</summary>"""
    # Подготовка
    gram = unit_model("грамм")
    convertor = reference_convertor()
    # Действие
    result = convertor.convert(gram, "unit")["unit"]
    # Проверка
    assert result == {
        "$id": "1", "$type": "unit_model", "$fields": {
            "name": "грамм", "coefficient": 1,
            "unique_code": gram.unique_code, "base_unit": {"$ref": "1"},
        },
    }
    assert gram.base_unit is gram


def test_shared_base_reference_convertor_convert_independent_branches():
    """<summary>Общий грамм определяется один раз; повторные ветки ссылаются на тот же ID.</summary>"""
    # Подготовка
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    milligram = unit_model("миллиграмм", 0.001, gram)
    source = [kilogram, gram, milligram]
    convertor = reference_convertor()
    # Действие
    result = convertor.convert(source)
    restored = reference_restore().restore(json.loads(json.dumps(result)))
    # Проверка
    values = result["value"]["$values"]
    base = values[0]["$fields"]["base_unit"]
    assert values[1] == {"$ref": base["$id"]}
    assert values[2]["$fields"]["base_unit"] == {"$ref": base["$id"]}
    assert restored[0].base_unit is restored[1]
    assert restored[2].base_unit is restored[1]
    assert restored[1].base_unit is restored[1]
    assert restored[0].convert_to(1, restored[1]) == 1000
    assert restored[2].convert_to(1000, restored[1]) == 1


@pytest.mark.parametrize("kind", ["list", "dict", "object", "model", "unit", "mixed"])
def test_restored_cycle_reference_convertor_convert_supported_graph(kind):
    """<summary>Циклы списков, словарей и известных объектов восстанавливаются по идентичности.</summary>"""
    # Подготовка
    if kind == "list":
        source = []
        source.append(source)
    elif kind == "dict":
        source = {}
        source["self"] = source
    elif kind == "mixed":
        source = {"rows": []}
        source["rows"].append(source)
    else:
        if kind == "unit":
            source = unit_model("грамм")
        elif kind == "model":
            source = abstract_model()
        else:
            source = SimpleNamespace()
        source.link = source
    convertor = reference_convertor()
    # Действие
    data = json.loads(json.dumps(convertor.convert(source)))
    restored = reference_restore().restore(data)
    # Проверка
    if kind == "list":
        assert restored[0] is restored
    elif kind == "dict":
        assert restored["self"] is restored
    elif kind == "mixed":
        assert restored["rows"][0] is restored
    else:
        assert restored.link is restored
        if kind == "unit":
            assert restored.base_unit is restored


def test_identity_tracking_reference_convertor_convert_equal_codes():
    """<summary>Разные экземпляры с одинаковым доменным кодом имеют разные служебные ID.</summary>"""
    # Подготовка
    first = abstract_model()
    second = abstract_model()
    second.unique_code = first.unique_code
    first.link = second
    source = [first, second]
    # Действие
    result = reference_convertor().convert(source)
    restored = reference_restore().restore(result)
    # Проверка
    assert restored[0] is not restored[1]
    assert restored[0].link is restored[1]
    assert restored[0].unique_code == restored[1].unique_code == first.unique_code


def test_preserved_tuple_reference_convertor_convert_cycle_through_list():
    """<summary>Неизменяемый tuple сохраняет тип и обратную ссылку через вложенный список.</summary>"""
    # Подготовка
    values = []
    source = (values,)
    values.append(source)
    # Действие
    result = reference_restore().restore(reference_convertor().convert(source))
    # Проверка
    assert isinstance(result, tuple)
    assert result[0][0] is result


def test_preserved_keys_reference_convertor_convert_reserved_and_typed_keys():
    """<summary>Пользовательские $id/$ref, числовые и tuple-ключи не смешиваются с метаданными.</summary>"""
    # Подготовка
    shared = [1, None]
    source = {"$id": "user value", "$ref": shared, 7: shared, ("a", 1): False}
    # Действие
    data = json.loads(json.dumps(reference_convertor().convert(source)))
    result = reference_restore().restore(data)
    # Проверка
    assert result == source
    assert result["$ref"] is result[7]
    assert ("a", 1) in result


def test_retained_objects_reference_convertor_convert_temporary_properties():
    """<summary>Временные tuple из getters удерживаются контекстом и получают разные ID.</summary>"""
    # Подготовка
    class tuple_source:
        """Создаёт отдельный временный tuple при каждом чтении свойства."""

        @property
        def first(self):
            """Возвращает первый временный tuple."""
            return tuple([1])

        @property
        def second(self):
            """Возвращает второй временный tuple."""
            return tuple([2])

    source = tuple_source()
    context = conversion_context_dto()
    # Действие
    result = reference_convertor().convert(source, context=context)["value"]["$fields"]
    # Проверка
    assert result["first"]["$values"] == [1]
    assert result["second"]["$values"] == [2]
    assert result["first"]["$id"] != result["second"]["$id"]
    assert len(context.objects) == 3
    assert context.path == []


@pytest.mark.parametrize("source", [b"data", {1, 2}, object()])
def test_arguments_exception_convert_factory_create_unsupported_type(source):
    """<summary>Неподдерживаемые типы отклоняются вместо потери данных.</summary>"""
    # Подготовка
    factory = convert_factory()
    # Действие
    with pytest.raises(arguments_exception) as error:
        factory.create(source)
    # Проверка
    assert "не поддерживается" in str(error.value)


def test_shared_context_reference_convertor_convert_independent_operations():
    """<summary>Вложения используют общий контекст, внешние вызовы получают разные реестры.</summary>"""
    # Подготовка
    source = {"first": "flour", "second": ["sugar"]}
    convertor = reference_convertor()
    original_convert = basic_convertor.convert
    contexts = []

    def record_convert(self, value, field_name="value", context=None):
        """Сохраняет переданный контекст, продолжая настоящее преобразование."""
        contexts.append(context)
        return original_convert(self, value, field_name, context)

    # Действие
    with patch.object(basic_convertor, "convert", autospec=True, side_effect=record_convert):
        first = convertor.convert(source)
        first_context = contexts[0]
        contexts.clear()
        second = convertor.convert(source)
    # Проверка
    assert first == second
    assert all(context is contexts[0] for context in contexts)
    assert contexts[0] is not first_context
    assert first_context.path == contexts[0].path == []
    assert first_context.object_ids and contexts[0].object_ids
