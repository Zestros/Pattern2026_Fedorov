"""Интеграционные проверки номенклатуры через HTTP, сервис и хранилище."""
import pytest

from Src.Api.application import create_app
from Src.Logics.storage_manager import storage_manager
from Src.Logics.settings_manager import setting_manager
from Src.Models.item_model import item_model
from Src.Models.recipe_item_model import recipe_item_model


@pytest.fixture
def catalog(monkeypatch):
    """Создаёт HTTP-клиент с изолированными настройками и хранилищем."""
    monkeypatch.setattr(storage_manager, "_storage_manager__instance", None)
    monkeypatch.delattr(setting_manager, "instance", raising=False)
    app = create_app().app
    return app.test_client(), app.extensions["report_storage"]


def payload(storage):
    """Готовит запрос номенклатуры со ссылками на существующий каталог."""
    return {
        "name": "Товар", "full_name": "Полное имя товара",
        "group": storage.groups[0].unique_code, "unit": storage.units[0].unique_code,
        "mass_ratio": {
            "value": 2,
            "unit": {"numerator_unit": storage.units[0].unique_code,
                     "denominator_unit": storage.units[0].unique_code},
        },
    }


def test_completed_item_routes_delegate_assembly_to_model(catalog, monkeypatch):
    """<summary>Маппер передаёт модели разрешённые ссылки при создании и только изменённые поля при PATCH.</summary>"""
    # Подготовка
    client, storage = catalog
    from_fields = item_model.from_fields
    updated_copy = item_model.updated_copy
    received = {}

    def record_creation(cls, fields, *, instance=None):
        """Записывает данные создания и передаёт их фабричному методу модели."""
        if instance is None:
            received["creation"] = fields.copy()
        return from_fields(fields, instance=instance)

    def record_update(model, fields):
        """Записывает поля PATCH и поручает модели собрать кандидат."""
        received["update"] = fields.copy()
        return updated_copy(model, fields)

    monkeypatch.setattr(item_model, "from_fields", classmethod(record_creation))
    monkeypatch.setattr(item_model, "updated_copy", record_update)

    # Действие
    created = client.post("/api/entities/item", json=payload(storage))
    location = created.headers["Location"]
    original_response = client.get(location)
    changed = client.patch(location, json={"name": "Новое имя"})
    deleted = client.delete(location)

    # Проверка
    assert created.status_code == 201
    assert received["creation"]["group"] is storage.groups[0]
    assert received["creation"]["unit"] is storage.units[0]
    assert received["update"] == {"name": "Новое имя"}
    assert original_response.json == created.json
    assert changed.status_code == 200
    assert changed.json["name"] == "Новое имя"
    assert changed.json["mass_ratio"] == created.json["mass_ratio"]
    assert deleted.status_code == 204


def test_preserved_identity_patch_item_omitted_and_null_ratio(catalog):
    """<summary>Пустой PATCH сохраняет объект характеристики массы, явный null удаляет её, идентичность номенклатуры сохраняется.</summary>"""
    # Подготовка
    client, storage = catalog
    created = client.post("/api/entities/item", json=payload(storage))
    location = created.headers["Location"]
    code = created.json["unique_code"]
    original = storage.find(item_model, code)
    ratio = original.mass_ratio
    # Действие
    unchanged = client.patch(location, json={})
    preserved_ratio = original.mass_ratio
    changed = client.patch(location, json={"mass_ratio": None})
    # Проверка
    assert changed.status_code == 200
    assert unchanged.json == created.json
    assert preserved_ratio is ratio
    assert changed.json["mass_ratio"] is None
    assert storage.find(item_model, code) is original
    assert original.mass_ratio is None


@pytest.mark.parametrize("change", [
    {"group": None}, {"unit": None}, {"name": None}, {"unique_code": None},
    {"group": "missing"}, {"recipe": "missing"}, {"output_quantity": None},
    {"unexpected": 1}, {"unique_code": "../bad"},
    {"mass_ratio": {"value": True, "unit": {}}},
    {"mass_ratio": {"value": 1, "unit": {"numerator_unit": "missing", "denominator_unit": "missing"}}},
])
def test_unchanged_state_patch_item_invalid_fields(catalog, change):
    """<summary>Недопустимое изменение возвращает HTTP 400 и сохраняет состояние, идентичность объекта и входящие ссылки.</summary>"""
    # Подготовка
    client, storage = catalog
    created = client.post("/api/entities/item", json=payload(storage))
    location = created.headers["Location"]
    model = storage.find(item_model, created.json["unique_code"])
    group = model.group
    owners = storage.find_references(type(group), group.unique_code)
    # Действие
    response = client.patch(location, json={"name": "Не сохранять", **change})
    # Проверка
    assert response.status_code == 400
    assert client.get(location).json == created.json
    assert storage.find(item_model, model.unique_code) is model
    assert storage.find_references(type(group), group.unique_code) == owners


def test_unchanged_state_patch_item_duplicate_code(catalog):
    """<summary>Попытка присвоить занятый код возвращает HTTP 409 и не сохраняет одновременно переданное новое имя.</summary>"""
    # Подготовка
    client, storage = catalog
    created = client.post("/api/entities/item", json=payload(storage))
    location = created.headers["Location"]
    # Действие
    response = client.patch(location, json={"name": "Не сохранять", "unique_code": storage.items[0].unique_code})
    # Проверка
    assert response.status_code == 409
    assert client.get(location).json == created.json


def test_preserved_identity_patch_product_cyclic_recipe(catalog):
    """<summary>Привязка продукта к содержащему его рецепту отклоняется без изменения состояния; последующее переименование успешно.</summary>"""
    # Подготовка
    client, storage = catalog
    product = next(item for item in storage.items if isinstance(item, recipe_item_model))
    location = f"/api/entities/item/{product.unique_code}"
    original_recipe = product.recipe
    original = client.get(location).json
    # Рецепт ссылается на продукт; привязка продукта к нему замкнула бы цикл.
    card = client.post("/api/entities/recipe", json={
        "name": "Циклическая карта", "mass_unit": original_recipe.mass_unit.unique_code,
        "ingredients": [{"item": product.unique_code, "quantity": 1}],
    })
    # Действие
    rejected = client.patch(location, json={"name": "Не сохранять", "recipe": card.json["unique_code"]})
    after_rejection = client.get(location).json
    recipe_after_rejection = product.recipe
    renamed = client.patch(location, json={"name": "Новое имя продукта"})
    # Проверка
    assert card.status_code == 201
    assert rejected.status_code == 400
    assert after_rejection == original
    assert recipe_after_rejection is original_recipe
    assert renamed.status_code == 200
    assert storage.find(item_model, product.unique_code) is product
    assert product.recipe is original_recipe


def test_preserved_references_patch_item_ratio_round_trip(catalog):
    """<summary>Повторная передача характеристики массы сохраняет вложенные идентификаторы и ссылки на те же единицы справочника.</summary>"""
    # Подготовка
    client, storage = catalog
    created = client.post("/api/entities/item", json=payload(storage))
    ratio = created.json["mass_ratio"]
    # Действие
    changed = client.patch(created.headers["Location"], json={"mass_ratio": ratio})
    # Проверка
    assert changed.status_code == 200
    assert changed.json == created.json
    model = storage.find(item_model, created.json["unique_code"])
    assert model.mass_ratio.unit.numerator_unit is storage.units[0]
    assert model.mass_ratio.unit.denominator_unit is storage.units[0]
