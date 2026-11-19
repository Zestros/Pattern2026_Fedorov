"""Интеграционные проверки сервиса, Mapper и настоящего хранилища."""
import pytest
from Src.Core.entity_model import entity_model
from Src.Dtos.entity_dto import entity_dto
from Src.Logics.dto_mapping import model_mapping, mapping_registry, dto_mapper
from Src.Logics.dto_serializer import dto_serializer
from Src.Logics.entity_service import entity_service
from Src.Logics.resource_catalog import resource_catalog, resource_definition
from Src.Logics.storage_manager import storage_manager
from Src.Models.settings_model import settings_model


class category_model(entity_model):
    """Новый справочник, о котором общий код ничего не знает."""
    def __init__(self, name: str) -> None:
        """Создаёт тестовую категорию с проверяемым именем."""
        super().__init__()
        self.name = name

class category_dto(entity_dto):
    """Контракт тестового справочника без специальных правил преобразования."""

@pytest.fixture
def empty_storage(monkeypatch):
    """Создаёт изолированное пустое хранилище без стартового каталога."""
    monkeypatch.setattr(storage_manager, "_storage_manager__instance", None)
    settings = settings_model()
    settings.first_start = False
    return storage_manager(settings)


def test_completed_entity_service_crud_new_registered_resource(empty_storage):
    """<summary>Новый справочник проходит создание, изменение и удаление
    в пустом хранилище после добавления только DTO и регистрации маппинга.</summary>"""
    # Подготовка
    registry = mapping_registry((model_mapping(category_dto, category_model),))
    resources = resource_catalog(registry, (resource_definition("category", category_dto),))
    service = entity_service(empty_storage, dto_mapper(registry, empty_storage, resources), resources)
    codec = dto_serializer()
    data = {"name": "Категория", "unique_code": "category-1"}

    # Действие
    initial = service.list("category")
    created = service.create(codec.deserialize(data, resources.request_type("category", data)))
    current = empty_storage.find(category_model, "category-1")
    changed = service.change("category", "category-1", codec.deserialize(
        {"name": "Другое имя"}, category_dto, partial=True))
    updated = empty_storage.find(category_model, "category-1")
    listing = codec.serialize(service.list("category"))
    service.delete("category", "category-1")
    remaining = service.list("category")

    # Проверка
    assert initial == ()
    assert codec.serialize(created) == data
    assert changed.name == "Другое имя"
    assert updated is current
    assert listing == [{"code": "category-1", "name": "Другое имя"}]
    assert remaining == ()

