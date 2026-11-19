"""Юнит-тесты менеджера хранения."""
import pytest

from Src.Core.entity_conflict_exception import entity_conflict_exception
from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Logics.storage_manager import storage_manager
from Src.Models.settings_model import settings_model
from Src.Models.warehouse_model import warehouse_model
from Src.Models.unit_model import unit_model
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.recipe_item_model import recipe_item_model
from Src.Models.recipe_ingredient_model import recipe_ingredient_model
from Src.Models.recipe_model import recipe_model


class warehouse_assignment_model(entity_model):
    """Тестовая сущность со ссылкой на склад без регистрации типа в хранилище."""

    def __init__(self, warehouse: warehouse_model) -> None:
        """Сохраняет склад, на который назначена сущность."""
        super().__init__()
        self.name = "Назначение склада"
        self.__warehouse = warehouse

    @property
    def warehouse(self) -> warehouse_model:
        """Возвращает склад, обнаруживаемый через параметр конструктора."""
        return self.__warehouse


@pytest.fixture(autouse=True)
def isolated_storage_manager(monkeypatch):
    """Изолирует Singleton между тестами и восстанавливает его после."""
    monkeypatch.setattr(
        storage_manager,
        "_storage_manager__instance",
        None,
    )


@pytest.fixture
def settings():
    """Создаёт настройки обычного запуска без первичных данных."""
    model = settings_model()
    model.first_start = False
    return model


@pytest.fixture
def manager(settings):
    """Создаёт пустое хранилище."""
    return storage_manager(settings)


@pytest.fixture
def models():
    """Создаёт связанные модели для проверки добавления."""
    group = group_model("Бакалея")
    unit = unit_model("килограмм")
    warehouse = warehouse_model("Основной склад")
    item = item_model("Мука", "Мука пшеничная", group, unit)

    return {
        "group": group,
        "unit": unit,
        "warehouse": warehouse,
        "item": item,
    }


def test_same_instance_storage_manager_repeated_creation(settings):
    """
    <summary>
    Повторное создание менеджера возвращает тот же экземпляр Singleton.
    </summary>
    """
    # Подготовка
    first = storage_manager(settings)

    # Действие
    second = storage_manager(settings)

    # Проверка
    assert first is second


def test_preserved_data_storage_manager_repeated_creation(settings):
    """
    <summary>
    Повторное создание менеджера не очищает добавленные данные.
    В хранилище остаётся тот же объект склада.
    </summary>
    """
    # Подготовка
    first = storage_manager(settings)
    warehouse = warehouse_model("Основной склад")
    first.add_warehouse(warehouse)

    # Действие
    second = storage_manager(settings)

    # Проверка
    assert len(second.warehouses) == 1
    assert second.warehouses[0] is warehouse


def test_empty_collections_storage_manager_regular_start(manager):
    """
    <summary>
    При first_start=False все коллекции остаются пустыми.
    Подготовка хранилища считается успешной.
    </summary>
    """
    # Подготовка
    # Используются входные данные, указанные в параметрах или вызове ниже.

    # Действие
    result = manager.is_loaded()

    # Проверка
    assert result is True
    assert manager.warehouses == ()
    assert manager.units == ()
    assert manager.items == ()
    assert manager.groups == ()
    assert manager.recipes == ()


@pytest.mark.parametrize(
    "method, collection, model_name",
    [
        ("add_warehouse", "warehouses", "warehouse"),
        ("add_unit", "units", "unit"),
        ("add_group", "groups", "group"),
        ("add_item", "items", "item"),
    ],
)
def test_added_model_storage_manager_valid_data(
    manager, models, method, collection, model_name
):
    """
    <summary>
    Каждый метод добавления сохраняет переданный объект в своей коллекции.
    Для номенклатуры предварительно регистрируются группа и единица.
    </summary>
    """
    # Подготовка
    model = models[model_name]
    if model_name == "item":
        manager.add_group(models["group"])
        manager.add_unit(models["unit"])

    # Действие
    getattr(manager, method)(model)

    # Проверка
    saved_models = getattr(manager, collection)
    assert len(saved_models) == 1
    assert saved_models[0] is model


@pytest.mark.parametrize(
    "method",
    ["add_warehouse", "add_unit", "add_group", "add_item"],
)
def test_arguments_exception_storage_manager_invalid_model(manager, method):
    """
    <summary>
    Методы добавления отклоняют значение неподходящего типа.
    Коллекции остаются пустыми.
    </summary>
    """
    # Подготовка
    # Используются входные данные, указанные в параметрах или вызове ниже.

    # Действие
    with pytest.raises(arguments_exception):
        getattr(manager, method)("не модель")

    # Проверка
    # pytest.raises проверяет ожидаемый тип исключения.
    assert not manager.warehouses
    assert not manager.units
    assert not manager.groups
    assert not manager.items


@pytest.mark.parametrize(
    "method, collection, model_name",
    [
        ("add_warehouse", "warehouses", "warehouse"),
        ("add_unit", "units", "unit"),
        ("add_group", "groups", "group"),
        ("add_item", "items", "item"),
    ],
)
def test_arguments_exception_storage_manager_repeated_model(
    manager, models, method, collection, model_name
):
    """
    <summary>
    Повторное добавление одного объекта вызывает arguments_exception.
    Дубликат не появляется в коллекции.
    </summary>
    """
    # Подготовка
    model = models[model_name]
    if model_name == "item":
        manager.add_group(models["group"])
        manager.add_unit(models["unit"])

    add_model = getattr(manager, method)
    add_model(model)

    # Действие
    with pytest.raises(arguments_exception):
        add_model(model)

    # Проверка
    assert len(getattr(manager, collection)) == 1


def test_arguments_exception_storage_manager_duplicate_code(manager):
    """
    <summary>
    Разные объекты с одинаковым кодом нельзя зарегистрировать.
    Проверка уникальности распространяется на разные коллекции.
    </summary>
    """
    # Подготовка
    warehouse = warehouse_model("Основной склад")
    group = group_model("Бакалея")
    group.unique_code = warehouse.unique_code
    manager.add_warehouse(warehouse)

    # Действие
    with pytest.raises(arguments_exception):
        manager.add_group(group)

    # Проверка
    assert not manager.groups
    assert manager.warehouses[0] is warehouse


@pytest.mark.parametrize("missing_relation", ["group", "unit"])
def test_arguments_exception_add_item_missing_relation(
    manager, models, missing_relation
):
    """
    <summary>
    Номенклатура не добавляется без зарегистрированной группы или единицы.
    При ошибке коллекция номенклатуры остаётся пустой.
    </summary>
    """
    # Подготовка
    if missing_relation != "group":
        manager.add_group(models["group"])
    if missing_relation != "unit":
        manager.add_unit(models["unit"])

    # Действие
    with pytest.raises(arguments_exception):
        manager.add_item(models["item"])

    # Проверка
    assert not manager.items


def test_arguments_exception_add_unit_missing_base(manager):
    """
    <summary>
    Производная единица не добавляется, пока её базовая единица
    не зарегистрирована в хранилище.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)

    # Действие
    with pytest.raises(arguments_exception):
        manager.add_unit(kilogram)

    # Проверка
    assert not manager.units


def test_added_unit_add_unit_registered_base(manager):
    """
    <summary>
    Производная единица добавляется после регистрации базовой.
    Ссылка на базовую единицу и коэффициент сохраняются.
    </summary>
    """
    # Подготовка
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    manager.add_unit(gram)

    # Действие
    manager.add_unit(kilogram)

    # Проверка
    assert len(manager.units) == 2
    assert manager.units[1] is kilogram
    assert kilogram.base_unit is gram
    assert kilogram.coefficient == 1000


def test_filled_collections_storage_manager_first_start(settings):
    """
    <summary>
    Первый старт создаёт склад, группу, единицы измерения,
    четыре базовых продукта, тесто и пшеничные лепёшки.
    Все объекты имеют уникальные коды.
    </summary>
    """
    # Подготовка
    settings.first_start = True
    manager = storage_manager(settings)

    # Действие
    result = manager.is_loaded()

    # Проверка
    assert result is True
    assert len(manager.warehouses) == 1
    assert len(manager.groups) == 1
    assert len(manager.units) == 5
    assert len(manager.items) == 13
    assert manager.warehouses[0].name == "Основной склад"
    assert manager.groups[0].name == "Бакалея"
    assert {item.name for item in manager.items} == {
        "Мука", "Вода", "Масло", "Соль",
        "Тесто", "Пшеничные лепёшки", "Бисквитный торт",
        "Сахар", "Яйцо", "Сметана", "Бисквитный корж", "Порция крема",
    }
    assert len(manager.recipes) == 5

    # Действие
    all_models = (
        manager.warehouses
        + manager.groups
        + manager.units
        + manager.items
        + manager.recipes
    )
    codes = [model.unique_code for model in all_models]

    # Проверка
    assert all(codes)
    assert len(codes) == len(set(codes))


def test_preserved_data_convert_repeated_call(settings):
    """
    <summary>
    Повторный convert не пересоздаёт первичные данные.
    Состав коллекций и идентичность каждого объекта сохраняются.
    </summary>
    """
    # Подготовка
    settings.first_start = True
    manager = storage_manager(settings)
    previous = (
        manager.warehouses,
        manager.units,
        manager.items,
        manager.groups,
    )

    # Действие
    result = manager.convert()

    # Проверка
    assert result is True
    current = (
        manager.warehouses,
        manager.units,
        manager.items,
        manager.groups,
    )

    for before, after in zip(previous, current):
        assert len(before) == len(after)
        assert all(old is new for old, new in zip(before, after))


def test_created_recipes_storage_manager_first_start(settings):
    """
    <summary>
    Лепёшки содержат полуфабрикат «Тесто».
    Карта теста использует зарегистрированные продукты.
    Массы соответствуют рецепту из Markdown.
    </summary>
    """
    # Подготовка
    settings.first_start = True
    manager = storage_manager(settings)
    dough = next(item for item in manager.items if item.name == "Тесто")

    # Действие
    bread = next(item for item in manager.items if item.name == "Пшеничные лепёшки")

    # Проверка
    assert isinstance(dough, recipe_item_model)
    assert isinstance(bread, recipe_item_model)
    assert len(dough.recipe.ingredients) == 4

    # Действие
    composition = {
        row.item.name: row.quantity
        for row in dough.recipe.ingredients
    }

    # Проверка
    assert composition == {
        "Мука": 0.3,
        "Вода": 0.18,
        "Масло": 0.015,
        "Соль": 0.005,
    }

    # Действие
    for row in dough.recipe.ingredients:
        assert row.item is manager.find(item_model, row.item.unique_code)

    # Проверка
    assert len(bread.recipe.ingredients) == 1

    # Действие
    dough_row = bread.recipe.ingredients[0]

    # Проверка
    assert dough_row.item is dough
    assert dough_row.quantity == pytest.approx(0.4985)
    assert dough.recipe.gross_weight == pytest.approx(498.5)
    assert dough.recipe.net_weight == pytest.approx(498.5)
    assert bread.output_quantity == 6
    assert bread.recipe.mass_coefficient == pytest.approx(0.9)
    assert bread.recipe.gross_weight == pytest.approx(498.5)
    assert bread.recipe.net_weight == pytest.approx(448.65)

    # Действие
    gram = dough.recipe.mass_unit

    # Действие
    result = bread.calculate_mass(1, gram)

    # Проверка
    assert result == pytest.approx(74.775)


def test_preserved_recipes_storage_manager_repeated_initialization(settings):
    """
    <summary>
    Повторное создание менеджера и вызов convert не создают
    новые продукты, карты или строки рецептов.
    </summary>
    """
    # Подготовка
    settings.first_start = True
    first = storage_manager(settings)
    previous_items = first.items
    bread = next(
        item for item in first.items
        if item.name == "Пшеничные лепёшки"
    )
    previous_recipe = bread.recipe
    previous_row = bread.recipe.ingredients[0]
    second = storage_manager(settings)

    # Действие
    second.convert()

    # Проверка
    assert second is first
    assert len(second.items) == len(previous_items)
    assert all(
        before is after
        for before, after in zip(previous_items, second.items)
    )
    assert bread.recipe is previous_recipe
    assert bread.recipe.ingredients[0] is previous_row
    assert bread.recipe.net_weight == pytest.approx(448.65)


def test_registered_recipe_storage_manager_add_and_find(manager, models):
    """<summary>Самостоятельная карта и продукт используют один экземпляр карты из репозитория.</summary>"""
    # Подготовка
    group, unit, item = (models[name] for name in ("group", "unit", "item"))
    manager.add(group_model, group)
    manager.add(unit_model, unit)
    manager.add(item_model, item)
    recipe = recipe_model("Технологическая карта", unit)
    recipe.add_ingredient(item, 1)
    product = recipe_item_model("Хлеб", "Хлеб пшеничный", group, unit, recipe)

    # Действие
    manager.add(recipe_model, recipe)
    manager.add(item_model, product)

    # Проверка
    assert manager.list(recipe_model) == (recipe,)
    assert manager.find(recipe_model, recipe.unique_code) is product.recipe
    assert recipe.ingredients[0].item is manager.find(item_model, item.unique_code)
    assert manager.find(item_model, recipe.unique_code) is None


def test_unchanged_storage_manager_add_recipe_with_unregistered_ingredient(manager, models):
    """<summary>Карта отклоняется, если её строка указывает на копию зарегистрированного продукта.</summary>"""
    # Подготовка
    group, unit, item = (models[name] for name in ("group", "unit", "item"))
    manager.add(group_model, group)
    manager.add(unit_model, unit)
    manager.add(item_model, item)
    copy = item_model(item.name, item.full_name, group, unit)
    copy.unique_code = item.unique_code
    recipe = recipe_model("Технологическая карта", unit)
    recipe.add_ingredient(copy, 1)

    # Действие
    with pytest.raises(arguments_exception):
        manager.add(recipe_model, recipe)

    # Проверка
    assert not manager.recipes
    assert manager.find(item_model, item.unique_code) is item


def test_protected_unit_storage_manager_delete_and_change_code(settings):
    """<summary>Индекс находит прямые ссылки единиц, характеристик массы и рецептов.</summary>"""
    # Подготовка
    settings.first_start = True
    storage = storage_manager(settings)
    gram, kilogram, _, liter, _ = storage.units

    # Действие
    gram_owners = storage.find_references(unit_model, gram.unique_code)
    liter_owners = storage.find_references(unit_model, liter.unique_code)
    with pytest.raises(entity_conflict_exception):
        storage.delete(unit_model, gram.unique_code)
    with pytest.raises(entity_conflict_exception):
        storage.update(unit_model, gram.unique_code, {"unique_code": "gram"})
    updated = storage.update(unit_model, gram.unique_code, {"name": "г"})

    # Проверка
    assert any(owner is kilogram for owner in gram_owners)
    assert any(isinstance(owner, recipe_model) for owner in gram_owners)
    assert {owner.name for owner in liter_owners} == {"Вода", "Масло"}
    assert all(owner is not gram for owner in gram_owners)
    assert storage.find(unit_model, gram.unique_code) is gram
    assert updated is gram
    assert kilogram.base_unit is gram
    assert kilogram.base_unit.name == "г"


def test_updated_links_storage_manager_update_and_delete_recipe(manager, models):
    """<summary>Замена строк снимает старые ссылки и регистрирует новые, удаление карты освобождает товары.</summary>"""
    # Подготовка
    group, unit, item = (models[name] for name in ("group", "unit", "item"))
    manager.add(group_model, group)
    manager.add(unit_model, unit)
    manager.add(item_model, item)
    replacement = item_model("Сахар", "Сахар белый", group, unit)
    manager.add(item_model, replacement)
    recipe = recipe_model("Карта", unit)
    recipe.add_ingredient(item, 1)
    manager.add(recipe_model, recipe)
    product = recipe_item_model("Хлеб", "Хлеб пшеничный", group, unit, recipe)
    manager.add(item_model, product)

    new_line = recipe_ingredient_model(replacement, 2)

    # Действие
    updated = manager.update(recipe_model, recipe.unique_code, {"ingredients": [new_line]})
    deleted_item = manager.delete(item_model, item.unique_code)

    # Проверка
    assert updated is recipe
    assert product.recipe is recipe
    assert product.recipe.ingredients == (new_line,)
    assert recipe.net_weight == 2
    assert deleted_item
    assert manager.find_references(item_model, replacement.unique_code) == (recipe,)
    # Действие
    with pytest.raises(entity_conflict_exception):
        manager.delete(recipe_model, recipe.unique_code)
    deleted_product = manager.delete(item_model, product.unique_code)
    deleted_recipe = manager.delete(recipe_model, recipe.unique_code)
    deleted_replacement = manager.delete(item_model, replacement.unique_code)

    # Проверка
    assert deleted_product
    assert deleted_recipe
    assert deleted_replacement
    assert not manager.delete(item_model, replacement.unique_code)


def test_preserved_state_storage_manager_update_incompatible_recipe_unit(settings):
    """<summary>Несовместимое изменение карты откатывает её состояние и сохраняет входящие связи.</summary>"""
    # Подготовка
    settings.first_start = True
    storage = storage_manager(settings)
    dough = next(item for item in storage.items if item.name == "Тесто")
    recipe = dough.recipe
    previous_unit = recipe.mass_unit
    previous_name = recipe.name
    previous_rows = recipe.ingredients

    # Действие
    with pytest.raises(arguments_exception):
        storage.update(recipe_model, recipe.unique_code, {
            "name": "Другое тесто", "mass_unit": storage.units[-1],
        })

    # Проверка
    assert recipe.name == previous_name
    assert recipe.mass_unit is previous_unit
    assert recipe.ingredients == previous_rows
    assert recipe.net_weight == pytest.approx(498.5)
    assert storage.find_references(recipe_model, recipe.unique_code) == (dough,)

    # Действие
    with pytest.raises(arguments_exception, match="Циклическая ссылка"):
        storage.update(recipe_model, recipe.unique_code, {
            "ingredients": [recipe_ingredient_model(dough, 1)],
        })

    # Проверка
    assert recipe.ingredients == previous_rows
    assert storage.find_references(item_model, dough.unique_code) == (
        next(item.recipe for item in storage.items if item.name == "Пшеничные лепёшки"),
    )


def test_changed_code_storage_manager_update_unreferenced_unit(manager):
    """<summary>Смена кода переносит запись и исходящие связи без потери идентичности.</summary>"""
    # Подготовка
    gram = unit_model("грамм")
    kilogram = unit_model("килограмм", 1000, gram)
    manager.add(unit_model, gram)
    manager.add(unit_model, kilogram)
    old_code = kilogram.unique_code

    # Действие
    with pytest.raises(entity_conflict_exception):
        manager.update(unit_model, old_code, {"unique_code": gram.unique_code})
    with pytest.raises(arguments_exception, match="через репозиторий"):
        kilogram.unique_code = "outside"

    updated_kilogram = manager.update(unit_model, old_code, {"unique_code": "kg"})

    # Проверка
    assert updated_kilogram is kilogram
    assert manager.find(unit_model, old_code) is None
    assert manager.find(unit_model, "kg") is kilogram
    assert manager.find_references(unit_model, gram.unique_code) == (kilogram,)
    # Действие
    deleted_kilogram = manager.delete(unit_model, "kg")
    updated_gram = manager.update(unit_model, gram.unique_code, {"unique_code": "g"})
    deleted_gram = manager.delete(unit_model, "g")

    # Проверка
    assert deleted_kilogram
    assert updated_gram is gram
    assert gram.base_unit is gram
    assert deleted_gram


def test_indexed_new_type_storage_manager_update_reference_without_registry(manager):
    """<summary>Репозиторий индексирует связь нового типа и переносит её при обновлении без изменений в реестре.</summary>"""
    # Подготовка
    first = warehouse_model("Первый склад")
    second = warehouse_model("Второй склад")
    assignment = warehouse_assignment_model(first)
    manager.add(warehouse_model, first)
    manager.add(warehouse_model, second)
    manager.add(warehouse_assignment_model, assignment)

    # Действие
    listed = manager.list(warehouse_assignment_model)
    references = manager.find_references(warehouse_model, first.unique_code)
    with pytest.raises(entity_conflict_exception):
        manager.delete(warehouse_model, first.unique_code)
    updated = manager.update(warehouse_assignment_model, assignment.unique_code, {"warehouse": second})
    deleted = manager.delete(warehouse_model, first.unique_code)

    # Проверка
    assert listed == (assignment,)
    assert references == (assignment,)
    assert updated is assignment
    assert assignment.warehouse is second
    assert deleted
    assert manager.find_references(warehouse_model, second.unique_code) == (assignment,)
