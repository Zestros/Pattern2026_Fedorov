"""Интеграционные проверки поиска справочников и складской ОСВ."""

from datetime import datetime
import json
from pathlib import Path

import pytest

from Src.Api.application import create_app
from Src.Logics.convert_factory import convert_factory
from Src.Logics.reference_restore import reference_restore
from Src.Logics.settings_manager import setting_manager
from Src.Logics.storage_manager import storage_manager
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.transaction_model import transaction_model
from Src.Models.unit_model import unit_model
from Src.Models.warehouse_model import warehouse_model


# Период, покрывающий два граничных дня демонстрационных движений.
TURNOVER_URL = "/api/reports/turnover?date_from=2026-02-01&date_to=2026-02-28"


@pytest.fixture
def search_app(monkeypatch):
    """Создаёт HTTP-приложение со стартовым каталогом и пустым журналом движений."""
    monkeypatch.setattr(storage_manager, "_storage_manager__instance", None)
    monkeypatch.delattr(setting_manager, "instance", raising=False)
    load = setting_manager.load

    def load_test_settings(manager, file_name):
        """Использует каталог и явно задаёт режим загрузки движений для тестов."""
        load(manager, file_name)
        manager.settings.first_start = True
        manager.settings.seed_demo_transactions = False

    monkeypatch.setattr(setting_manager, "load", load_test_settings)
    return create_app().app


@pytest.mark.parametrize(
    "resource, name, path, value",
    [
        ("item", "Мука", "group.name", "бакал"),
        ("group", "Сухие продукты", "parent.name", "бакал"),
        ("unit", "килограмм", "base_unit.name", "ГРАММ"),
        ("recipe", "Тесто для пшеничных лепёшек", "ingredients.item.name", "МУК"),
    ],
)
def test_found_entity_search_entities_combines_code_and_nested_field(search_app, resource, name, path, value):
    """<summary>Каждый справочник поддерживает точный код вместе с поиском по вложенному полю.</summary>"""
    # Подготовка
    storage = search_app.extensions["report_storage"]
    storage.add_group(group_model("Сухие продукты", storage.groups[0]))
    collections = {"item": storage.items, "group": storage.groups, "unit": storage.units, "recipe": storage.recipes}
    entity = next(model for model in collections[resource] if model.name == name)
    criteria = {
        "filters": [
            {"field": "unique_code", "operator": "EQUALS", "value": entity.unique_code},
            {"field": path, "operator": "LIKE", "value": value},
        ],
    }

    # Действие
    response = search_app.test_client().post(f"/api/entities/{resource}/search", json=criteria)

    # Проверка
    assert response.status_code == 200
    assert response.get_json() == [{"code": entity.unique_code, "name": name}]


@pytest.mark.parametrize(("direction", "ordered_codes"), [
    ("ASC", ["child-b", "child-a", "child-c", "child-d"]),
    ("DESC", ["child-c", "child-b", "child-a", "child-d"]),
])
def test_sorted_groups_search_entities_respects_priorities_and_missing_parent(search_app, direction, ordered_codes):
    """<summary>Группы сортируются по имени владельца и своему имени, корневая группа идёт в конце.</summary>"""
    # Подготовка
    client = search_app.test_client()
    for fields in (
        {"name": "Альфа", "unique_code": "parent-a"},
        {"name": "Бета", "unique_code": "parent-b"},
        {"name": "Тест А", "unique_code": "child-a", "parent": "parent-a"},
        {"name": "Тест Б", "unique_code": "child-b", "parent": "parent-a"},
        {"name": "Тест В", "unique_code": "child-c", "parent": "parent-b"},
        {"name": "Тест Г", "unique_code": "child-d"},
    ):
        assert client.post("/api/entities/group", json=fields).status_code == 201

    # Действие
    response = client.post("/api/entities/group/search", json={
        "filters": [{"field": "name", "operator": "LIKE", "value": "тест"}],
        "sort": [{"field": "parent.name", "direction": direction}, {"field": "name", "direction": "DESC"}],
    })
    cycle = client.patch("/api/entities/group/parent-a", json={"parent": "child-a"})
    self_cycle = client.patch("/api/entities/group/parent-a", json={"parent": "parent-a"})

    # Проверка
    assert response.status_code == 200
    assert [row["code"] for row in response.get_json()] == ordered_codes
    assert cycle.status_code == self_cycle.status_code == 400
    assert client.get("/api/entities/group/parent-a").get_json()["parent"] is None


def test_found_descendants_search_entities_resolves_new_nested_path(search_app):
    """<summary>Поиск находит группу по имени владельца второго уровня без регистрации пути.</summary>"""
    # Подготовка
    storage = search_app.extensions["report_storage"]
    root = group_model("Продукты")
    parent = group_model("Бакалея для кухни", root)
    child = group_model("Крупы", parent)
    storage.register_models((child,))

    # Действие
    response = search_app.test_client().post("/api/entities/group/search", json={
        "filters": [{"field": "parent.parent.name", "operator": "EQUALS", "value": root.name}],
        "sort": [{"field": "parent.parent.unique_code"}],
    })

    # Проверка
    assert response.status_code == 200
    assert response.get_json() == [{"code": child.unique_code, "name": child.name}]


@pytest.mark.parametrize("filters", [
    [],
    [{"field": "unique_code", "operator": "EQUALS", "value": "missing-recipe"}],
])
def test_bad_request_search_entities_rejects_collection_sort(search_app, filters):
    """<summary>Сортировка по коллекции ингредиентов отклоняется и на пустой выборке.</summary>"""
    # Действие
    response = search_app.test_client().post("/api/entities/recipe/search", json={
        "filters": filters,
        "sort": [{"field": "ingredients.item.name"}],
    })

    # Проверка
    assert response.status_code == 400
    assert "Сортировка по коллекции недоступна: ingredients.item.name" in response.get_data(as_text=True)


@pytest.mark.parametrize("criteria", [
    {"filters": [{"field": "name", "operator": "INVALID", "value": "Мука"}]},
    {"filters": [{"field": "name", "operator": "LIKE", "value": " "}]},
    {"sort": [{"field": "group.__dict__"}]},
    {"sort": [{"field": "name", "direction": "INVALID"}]},
])
def test_bad_request_search_entities_rejects_invalid_criteria(search_app, criteria):
    """<summary>Неизвестные операции, поля, направления и пустой текст отклоняются с HTTP 400.</summary>"""
    response = search_app.test_client().post("/api/entities/item/search", json=criteria)

    assert response.status_code == 400


def test_balanced_rows_get_turnover_filters_and_sorts_movements(search_app):
    """<summary>ОСВ учитывает граничные даты, пересчёт единиц, фильтр и отдельные остатки складов.</summary>"""
    # Подготовка
    storage = search_app.extensions["report_storage"]
    flour = next(item for item in storage.items if item.name == "Мука")
    water = next(item for item in storage.items if item.name == "Вода")
    gram = flour.unit.base_unit
    main_warehouse = storage.warehouses[0]
    other_warehouse = warehouse_model("Второй склад")
    storage.register_models((
        transaction_model(datetime(2026, 1, 31, 23, 59), main_warehouse, flour, gram, 10),
        transaction_model(datetime(2026, 2, 1), main_warehouse, flour, flour.unit, 0.005),
        transaction_model(datetime(2026, 2, 28, 23, 59), main_warehouse, flour, gram, -3),
        transaction_model(datetime(2026, 3, 1), main_warehouse, flour, gram, 20),
        transaction_model(datetime(2026, 2, 10), main_warehouse, water, water.unit, 7),
        transaction_model(datetime(2026, 1, 20), other_warehouse, flour, gram, 2),
    ))

    # Действие
    response = search_app.test_client().post(TURNOVER_URL, json={
        "filters": [{"field": "item.name", "operator": "EQUALS", "value": "Мука"}],
        "sort": [{"field": "warehouse.name"}],
    })

    # Проверка
    assert response.status_code == 200
    rows = response.get_json()
    assert [row["warehouse_code"] for row in rows] == [other_warehouse.unique_code, main_warehouse.unique_code]
    assert all(row["item_code"] == flour.unique_code and row["unit_code"] == gram.unique_code for row in rows)
    assert [(row["opening"], row["receipts"], row["issues"], row["closing"]) for row in rows] == [
        (2, 0, 0, 2),
        (10, 5, 3, 12),
    ]


def test_combined_rows_get_turnover_keeps_opening_and_period_only_groups(search_app):
    """<summary>Общий фильтр и сортировка действуют на строки с остатком и строки с оборотами периода.</summary>"""
    # Подготовка
    storage = search_app.extensions["report_storage"]
    flour = next(item for item in storage.items if item.name == "Мука")
    water = next(item for item in storage.items if item.name == "Вода")
    hall = warehouse_model("Зал")
    bar = warehouse_model("Бар")
    storage.register_models((
        transaction_model(datetime(2026, 1, 31), hall, flour, flour.unit.base_unit, 4),
        transaction_model(datetime(2026, 2, 1), bar, flour, flour.unit.base_unit, 7),
        transaction_model(datetime(2026, 1, 31), bar, water, water.unit.base_unit, 2),
        transaction_model(datetime(2026, 2, 1), hall, water, water.unit.base_unit, 5),
    ))

    # Действие
    response = search_app.test_client().post(TURNOVER_URL, json={
        "filters": [{"field": "item.unique_code", "operator": "EQUALS", "value": flour.unique_code}],
        "sort": [{"field": "warehouse.name", "direction": "ASC"}],
    })

    # Проверка
    assert response.status_code == 200
    rows = response.get_json()
    assert [row["warehouse_name"] for row in rows] == ["Бар", "Зал"]
    assert all(row["item_code"] == flour.unique_code for row in rows)
    assert [(row["opening"], row["receipts"], row["issues"], row["closing"]) for row in rows] == [
        (0, 7, 0, 7),
        (4, 0, 0, 4),
    ]


@pytest.mark.parametrize("query", [
    "",
    "?date_from=20260201&date_to=2026-02-28",
    "?date_from=2026-03-01&date_to=2026-02-28",
])
def test_bad_request_get_turnover_rejects_invalid_period(search_app, query):
    """<summary>ОСВ отклоняет пропущенные даты, неправильный формат и обратные границы периода.</summary>"""
    response = search_app.test_client().post("/api/reports/turnover" + query, json={})

    assert response.status_code == 400


@pytest.mark.parametrize("first_start, seed, count", [(True, False, 0), (False, True, 0), (True, True, 5)])
def test_seeded_movements_storage_manager_respects_settings(monkeypatch, tmp_path, first_start, seed, count):
    """<summary>Демонстрационные движения создаются один раз, когда включены оба флага настроек.</summary>"""
    # Подготовка
    monkeypatch.setattr(storage_manager, "_storage_manager__instance", None)
    flags = {"first_start": first_start, "seed_demo_transactions": seed}
    default_path = Path(__file__).resolve().parents[2] / "settings.json"
    configured = tmp_path / "settings.json"
    configured.write_text(json.dumps(json.loads(default_path.read_text(encoding="utf-8")) | flags), encoding="utf-8")
    manager = object.__new__(setting_manager)
    manager.load(str(configured))

    # Действие
    storage = storage_manager(manager.settings)
    movements = storage.transactions
    storage.convert()

    # Проверка
    assert len(movements) == count
    assert storage.transactions == movements


def test_restored_movements_reference_restore_keeps_canonical_quantity(search_app):
    """<summary>Снимок восстанавливает количество и общие ссылки движения на склад, товар и базовую единицу.</summary>"""
    # Подготовка
    storage = search_app.extensions["report_storage"]
    flour = next(item for item in storage.items if item.name == "Мука")
    movement = transaction_model(datetime(2026, 2, 1), storage.warehouses[0], flour, flour.unit, -0.005)
    storage.add(transaction_model, movement)

    # Действие
    data = convert_factory().create(storage).convert(storage)
    restored = reference_restore().restore(data)
    row, = restored.transactions

    # Проверка
    assert row.unique_code == movement.unique_code
    assert row.occurred_at == movement.occurred_at
    assert row.quantity == -5
    assert row.item is restored.find(item_model, flour.unique_code)
    assert row.warehouse is restored.warehouses[0]
    assert row.unit is restored.find(unit_model, flour.unit.base_unit.unique_code)
