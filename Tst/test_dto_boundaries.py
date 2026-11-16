"""Модульные проверки неизменяемости DTO и изоляции реестров."""
import pytest
from Src.Dtos.group_dto import group_dto
from Src.Logics.dto_serializer import dto_serializer
from Src.Logics.entity_mappings import entity_mappings, entity_resources


@pytest.mark.parametrize("field,value", [("name", "Новое имя"), ("unique_code", "new-code")])
def test_attribute_error_setattr_dto_existing_and_omitted_fields(field, value):
    """<summary>Присваивание существующего или пропущенного поля DTO запрещено;
    сериализация и сведения о присутствии полей остаются согласованными.</summary>"""
    # Подготовка
    dto = group_dto(name="Группа")
    codec = dto_serializer()
    previous = codec.serialize(dto)

    # Действие
    with pytest.raises(AttributeError):
        setattr(dto, field, value)

    # Проверка
    assert codec.serialize(dto) == previous
    assert dto.contains("name")
    assert not dto.contains("unique_code")


def test_attribute_error_delattr_dto_declared_field():
    """<summary>Удаление поля DTO запрещено и не оставляет несогласованной
    записи о присутствующем, но отсутствующем значении.</summary>"""
    # Подготовка
    dto = group_dto(name="Группа")

    # Действие
    with pytest.raises(AttributeError):
        del dto.name

    # Проверка
    assert dto.contains("name")
    assert dto.field_value("name") == "Группа"


def test_selected_request_type_resource_catalog_separate_mapping():
    """<summary>Каталог ресурсов выбирает внешний контракт; реестр маппинга
    отвечает только за соответствие выбранного DTO доменной модели.</summary>"""
    # Подготовка
    mappings = entity_mappings()
    resources = entity_resources(mappings)

    # Действие
    base = resources.request_type("item", {})
    variant = resources.request_type("item", {"recipe": "card"})
    base_mapping = mappings.for_type(base)
    variant_mapping = mappings.for_type(variant)

    # Проверка
    assert base is not variant
    assert issubclass(variant_mapping.model, base_mapping.model)
    assert resources.model_type("item") is base_mapping.model
