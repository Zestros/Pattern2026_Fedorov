"""Интеграционные проверки HTTP-маршрутов отчётности."""
import pytest
import yaml
from connexion.spec import Specification
import main
from Src.Api.application import create_app
from Src.Core.report_type_enum import report_type_enum
from Src.Logics.report_factory import report_factory
from Src.Logics.storage_manager import storage_manager
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.recipe_model import recipe_model
from Src.Models.settings_model import settings_model


@pytest.mark.parametrize('kind', ['item', 'unit', 'recipe'])
@pytest.mark.parametrize('format_', list(report_type_enum))
def test_correct_response_get_explicit_format(kind, format_):
    """<summary>Все типы сущностей доступны во всех форматах с правильной выдачей.</summary>"""
    # Подготовка
    entity = {'item': main.api.app.extensions["report_storage"].items[0], 'unit': main.api.app.extensions["report_storage"].units[0],
              'recipe': next(x.recipe for x in main.api.app.extensions["report_storage"].items if isinstance(x, recipe_item_model))}[kind]
    client = main.api.app.test_client()
    # Действие
    response = client.get(f'/api/reports/{kind}/{entity.unique_code}?format={format_.name}')
    # Проверка
    assert response.status_code == 200
    assert entity.unique_code in response.get_data(as_text=True)
    assert ('attachment' in response.headers.get('Content-Disposition', '')) == (format_.name in ('CSV', 'MARKDOWN'))
    assert response.mimetype == {'TXT':'text/plain','CSV':'text/csv','MARKDOWN':'text/markdown','XML':'application/xml','HTML':'text/html'}[format_.name]


def test_default_format_get_settings(monkeypatch):
    """<summary>Маршрут default выбирает Markdown из настроек и отдаёт файл.</summary>"""
    # Подготовка
    monkeypatch.setattr(main.api.app.extensions["report_settings"].settings, 'response_format', report_type_enum.MARKDOWN)
    client = main.api.app.test_client()
    # Действие
    response = client.get(f'/api/reports/unit/{main.api.app.extensions["report_storage"].units[0].unique_code}/default')
    # Проверка
    assert response.status_code == 200
    assert response.mimetype == 'text/markdown'
    assert '.md' in response.headers['Content-Disposition']


@pytest.mark.parametrize('url,status', [
    ('/api/reports/unit/missing?format=XML',404),
    ('/api/reports/unit/missing/default',404),
    ('/api/reports/wrong/missing?format=TXT',400),
    ('/api/reports/unit/missing?format=PDF',400),
    ('/api/reports/unit/missing',400),
])
def test_error_response_get_invalid_request(url,status):
    """<summary>Ошибки параметров и отсутствующий код имеют ожидаемый HTTP-статус.</summary>"""
    # Подготовка
    client = main.api.app.test_client()
    # Действие
    response = client.get(url)
    # Проверка
    assert response.status_code == status


def test_visible_recipe_get_entities_independently_registered_card(monkeypatch):
    """<summary>Самостоятельный рецепт появляется в списке и доступен для отчёта по своему коду.</summary>"""
    # Подготовка
    monkeypatch.setattr(storage_manager, "_storage_manager__instance", None)
    app = create_app().app
    storage = app.extensions["report_storage"]
    recipe = recipe_model("Черновик рецепта", storage.units[0])
    storage.add(recipe_model, recipe)
    client = app.test_client()

    # Действие
    listing = client.get("/api/entities/recipe")
    report = client.get(f"/api/reports/recipe/{recipe.unique_code}?format=TXT")

    # Проверка
    assert listing.status_code == 200
    assert {"code": recipe.unique_code, "name": recipe.name} in listing.get_json()
    assert report.status_code == 200
    assert recipe.unique_code in report.get_data(as_text=True)


@pytest.fixture
def crud_client(monkeypatch):
    """Создаёт HTTP-клиент с отдельным хранилищем для каждого теста."""
    monkeypatch.setattr(storage_manager, "_storage_manager__instance", None)
    return create_app().test_client()


@pytest.mark.parametrize("kind", ["group", "warehouse", "unit", "item", "recipe"])
def test_completed_crud_entity_routes(crud_client, kind):
    """<summary>Каждый тип создаётся, читается, меняется и удаляется через HTTP.</summary>"""
    # Подготовка
    endpoint = f"/api/entities/{kind}"
    group = crud_client.get("/api/entities/group").json()[0]["code"]
    unit = crud_client.get("/api/entities/unit").json()[0]["code"]
    item = crud_client.get("/api/entities/item").json()[0]["code"]
    fields = {
        "group": {},
        "warehouse": {},
        "unit": {},
        "item": {"full_name": "Учётная позиция", "group": group, "unit": unit},
        "recipe": {"mass_unit": unit, "ingredients": [{"item": item, "quantity": 1}]},
    }[kind]

    # Действие
    created = crud_client.post(endpoint, json={"name": "Новая сущность", **fields})
    location = created.headers["Location"]
    original = crud_client.get(location)
    updated = crud_client.patch(location, json={"name": "Новое имя", "unique_code": f"new-{kind}"})
    listing = crud_client.get(endpoint)
    retired_code = crud_client.get(location)
    new_location = f"{endpoint}/new-{kind}"
    deleted = crud_client.delete(new_location)
    missing = crud_client.get(new_location)

    # Проверка
    assert created.status_code == 201
    assert original.status_code == 200
    assert original.json() == created.json()
    assert all(original.json()[name] == value for name, value in fields.items() if name != "ingredients")
    if kind == "recipe":
        assert [row["item"] for row in original.json()["ingredients"]] == [item]
        assert original.json()["net_weight"] == 1000
    assert updated.status_code == 200
    assert updated.json()["unique_code"] == f"new-{kind}"
    assert {"code": f"new-{kind}", "name": "Новое имя"} in listing.json()
    assert retired_code.status_code == 404
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert missing.status_code == 404


def test_conflict_entity_routes_preserves_linked_entity(crud_client):
    """<summary>Связанный объект защищён от удаления и смены кода до разрыва связи.</summary>"""
    # Подготовка
    units = "/api/entities/unit"
    base = crud_client.post(units, json={"name": "База", "unique_code": "base"})
    derived = crud_client.post(units, json={
        "name": "Производная", "base_unit": "base", "coefficient": 2, "unique_code": "derived",
    })
    base_url = base.headers["Location"]
    derived_url = derived.headers["Location"]

    # Действие
    blocked_delete = crud_client.delete(base_url)
    blocked_code = crud_client.patch(base_url, json={"name": "Откат", "unique_code": "other"})
    current = crud_client.get(base_url)
    renamed = crud_client.patch(base_url, json={"name": "Новое имя базы"})
    linked = crud_client.get(derived_url)
    freed = crud_client.patch(derived_url, json={"base_unit": None, "coefficient": 1})
    deleted = crud_client.delete(base_url)

    # Проверка
    assert blocked_delete.status_code == blocked_code.status_code == 409
    assert current.json() == base.json()
    assert renamed.status_code == 200
    assert linked.json()["base_unit"] == "base"
    assert freed.status_code == 200
    assert freed.json()["base_unit"] == "derived"
    assert deleted.status_code == 204


def test_rejected_entity_routes_invalid_body_and_relation(crud_client):
    """<summary>Некорректный JSON и ссылки дают 400, а дубликат кода даёт 409.</summary>"""
    # Подготовка
    groups = "/api/entities/group"
    group = crud_client.post(groups, json={"name": "Группа", "unique_code": "existing"})
    unit = crud_client.get("/api/entities/unit").json()[0]["code"]
    items = "/api/entities/item"
    previous_items = crud_client.get(items).json()

    # Действие
    malformed = crud_client.post(groups, content="{", headers={"Content-Type": "application/json"})
    duplicate = crud_client.post(groups, json=group.json())
    invalid_item = crud_client.post(items, json={
        "name": "Товар", "full_name": "Товар", "group": "missing", "unit": unit,
    })
    invalid_patch = crud_client.patch(group.headers["Location"], json={"name": ""})
    current = crud_client.get(group.headers["Location"])
    current_items = crud_client.get(items)

    # Проверка
    assert malformed.status_code == invalid_item.status_code == invalid_patch.status_code == 400
    assert duplicate.status_code == 409
    assert current.json() == group.json()
    assert current_items.json() == previous_items


def test_updated_recipe_entity_routes_changes_links_and_report(crud_client):
    """<summary>Обновление состава и связи продукта с картой проходят через HTTP и индекс хранилища.</summary>"""
    # Подготовка
    group = crud_client.get("/api/entities/group").json()[0]["code"]
    gram = crud_client.get("/api/entities/unit").json()[0]["code"]
    item = crud_client.get("/api/entities/item").json()[0]["code"]
    card = crud_client.post("/api/entities/recipe", json={"name": "Карта", "mass_unit": gram})
    code = card.json()["unique_code"]
    card_url = card.headers["Location"]
    product = crud_client.post("/api/entities/item", json={
        "name": "Продукт", "full_name": "Продукт по карте", "group": group,
        "unit": gram, "recipe": code,
    })
    product_url = product.headers["Location"]

    # Действие
    updated = crud_client.patch(card_url, json={"ingredients": [{"item": item, "quantity": 2}]})
    invalid = crud_client.patch(card_url, json={
        "ingredients": [{"item": product.json()["unique_code"], "quantity": 1}],
    })
    current = crud_client.get(card_url)
    report = crud_client.get(f"/api/reports/recipe/{code}?format=TXT")
    blocked = crud_client.delete(card_url)
    deleted_product = crud_client.delete(product_url)
    deleted_recipe = crud_client.delete(card_url)

    # Проверка
    assert card.status_code == product.status_code == 201
    assert updated.status_code == current.status_code == report.status_code == 200
    assert updated.json()["net_weight"] == 2000
    assert product.json()["recipe"] == code
    assert invalid.status_code == 400
    assert current.json() == updated.json()
    assert code in report.text
    assert blocked.status_code == 409
    assert deleted_product.status_code == deleted_recipe.status_code == 204


def test_documented_api_routes_swagger_and_report_formats(crud_client):
    """<summary>Swagger ссылается на актуальную спецификацию, а список форматов совпадает с фабрикой.</summary>"""
    # Подготовка
    expected_formats = [format_.name for format_ in report_factory(settings_model()).formats()]

    # Действие
    ui = crud_client.get("/ui/")
    spec = crud_client.get("/openapi.yaml")
    formats = crud_client.get("/api/reports/formats")
    document = yaml.safe_load(spec.text)
    Specification.from_dict(document)
    actual = {
        (rule.rule.replace("<entity_type>", "{entity_type}").replace("<code>", "{code}"), method.lower())
        for rule in crud_client.app.app.url_map.iter_rules()
        if rule.rule.startswith("/api/")
        for method in rule.methods - {"HEAD", "OPTIONS"}
    }
    documented = {
        (path, method)
        for path, operations in document["paths"].items()
        for method in operations if method not in {"parameters"}
    }

    # Проверка
    assert ui.status_code == spec.status_code == formats.status_code == 200
    assert "/openapi.yaml" in ui.text
    assert document["servers"] == [{"url": "/"}]
    assert actual == documented
    assert formats.json() == expected_formats
