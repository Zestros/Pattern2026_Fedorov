"""Модульные проверки контрактов DTO и общего сериализатора."""
import pytest
from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Dtos.entity_dto import entity_dto
from Src.Dtos.group_dto import group_dto
from Src.Dtos.item_dto import item_dto, mass_ratio_dto
from Src.Dtos.recipe_dto import recipe_dto
from Src.Logics.dto_serializer import dto_serializer
from Src.Logics.entity_mappings import entity_mappings, entity_resources


class category_model(entity_model):
    """Новый справочник, о котором общий код ничего не знает."""
    def __init__(self, name: str) -> None:
        """Создаёт тестовую категорию с проверяемым именем."""
        super().__init__()
        self.name = name


class category_dto(entity_dto):
    """Контракт тестового справочника без специальных правил преобразования."""






@pytest.mark.parametrize("target,data", [
    (group_dto, {}), (group_dto, {"name": None}),
    (group_dto, {"name": "Группа", "unique_code": None}),
    (group_dto, {"name": "Группа", "$type": "os.system"}),
    (group_dto, {"name": "Группа", "_private": "value"}),
    (item_dto, {"name": "x", "full_name": "x", "group": [], "unit": "u"}),
    (mass_ratio_dto, {"value": True, "unit": {}}),
    (mass_ratio_dto, {"value": float("nan"), "unit": {}}),
    (mass_ratio_dto, {"value": float("inf"), "unit": {}}),
])
def test_arguments_exception_deserialize_invalid_contract(target, data):
    """<summary>Некорректные типы, отсутствующие обязательные и неизвестные поля отклоняются до создания модели.</summary>"""
    # Подготовка
    codec = dto_serializer()

    # Действие
    with pytest.raises(arguments_exception) as error:
        codec.deserialize(data, target)

    # Проверка
    assert isinstance(error.value, arguments_exception)


def test_preserved_presence_deserialize_partial_item():
    """<summary>Пустое изменение не содержит характеристики массы, а явный null сохраняется как команда очистки.</summary>"""
    # Подготовка
    codec = dto_serializer()

    # Действие
    absent = codec.deserialize({}, item_dto, partial=True)
    cleared = codec.deserialize({"mass_ratio": None}, item_dto, partial=True)
    # Проверка
    assert not absent.contains("mass_ratio")
    assert cleared.contains("mass_ratio")
    assert codec.serialize(absent) == {}
    assert codec.serialize(cleared) == {"mass_ratio": None}


def test_arguments_exception_deserialize_incomplete_nested_value():
    """<summary>Замена вложенной характеристики массы требует полного объекта, даже при частичном изменении номенклатуры.</summary>"""
    # Подготовка
    codec = dto_serializer()
    data = {"mass_ratio": {"value": 1}}

    # Действие
    with pytest.raises(arguments_exception) as error:
        codec.deserialize(data, item_dto, partial=True)

    # Проверка
    assert isinstance(error.value, arguments_exception)


@pytest.mark.parametrize("field", ["packaging_weight", "gross_weight", "net_weight"])
def test_arguments_exception_deserialize_computed_recipe_field(field):
    """<summary>Передача расчётной массы в частичном запросе рецепта отклоняется как изменение поля только для чтения.</summary>"""
    # Подготовка
    codec = dto_serializer()
    data = {field: 1}

    # Действие
    with pytest.raises(arguments_exception) as error:
        codec.deserialize(data, recipe_dto, partial=True)

    # Проверка
    assert isinstance(error.value, arguments_exception)


def test_arguments_exception_resource_unknown_name():
    """<summary>Поиск незарегистрированного ресурса завершается ошибкой без обращения к коллекциям хранилища.</summary>"""
    # Подготовка
    registry = entity_resources(entity_mappings())

    # Действие
    with pytest.raises(arguments_exception) as error:
        registry.resource("unknown")

    # Проверка
    assert isinstance(error.value, arguments_exception)


def test_arguments_exception_deserialize_undeclared_model_property(monkeypatch):
    """<summary>Добавленное свойство модели не становится доступным в API без объявления соответствующего поля DTO.</summary>"""
    # Подготовка
    codec = dto_serializer()
    monkeypatch.setattr(category_model, "secret", property(lambda self: "hidden"), raising=False)

    # Действие
    with pytest.raises(arguments_exception) as error:
        codec.deserialize({"name": "x", "secret": "changed"}, category_dto)

    # Проверка
    assert isinstance(error.value, arguments_exception)


def test_preserved_value_deserialize_nested_ratio():
    """<summary>Поле value вложенного DTO сохраняет число и не конфликтует со служебными методами DTO.</summary>"""
    # Подготовка
    codec = dto_serializer()
    data = {"value": 2, "unit": {"numerator_unit": "u", "denominator_unit": "u"}}

    # Действие
    dto = codec.deserialize(data, mass_ratio_dto)

    # Проверка
    assert dto.value == 2
    assert dto_serializer().serialize(dto)["value"] == 2
