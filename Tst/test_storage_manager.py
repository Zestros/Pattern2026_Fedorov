"""Юнит-тесты менеджера хранения."""
import pytest

from Src.Core.exception import arguments_exception
from Src.Logics.storage_manager import storage_manager
from Src.Models.settings_model import settings_model
from Src.Models.warehouse_model import warehouse_model
from Src.Models.unit_model import unit_model
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model


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
    # Проверка
    assert manager.is_loaded() is True
    assert manager.warehouses == ()
    assert manager.units == ()
    assert manager.items == ()
    assert manager.groups == ()


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
    # Действие
    with pytest.raises(arguments_exception):
        getattr(manager, method)("не модель")

    # Проверка
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
    Первый старт создаёт основной склад, группу Бакалея, грамм,
    килограмм и муку. Номенклатура использует общие объекты справочников.
    Коды всех созданных объектов уникальны.
    </summary>
    """
    # Подготовка
    settings.first_start = True

    # Действие
    manager = storage_manager(settings)

    # Проверка
    assert manager.is_loaded() is True
    assert len(manager.warehouses) == 1
    assert len(manager.groups) == 1
    assert len(manager.units) == 2
    assert len(manager.items) == 1

    assert manager.warehouses[0].name == "Основной склад"
    assert manager.groups[0].name == "Бакалея"

    units = {unit.name: unit for unit in manager.units}
    gram = units["грамм"]
    kilogram = units["килограмм"]

    assert gram.base_unit is gram
    assert gram.coefficient == 1
    assert kilogram.base_unit is gram
    assert kilogram.coefficient == 1000

    flour = manager.items[0]
    assert flour.name == "Мука"
    assert flour.full_name == "Мука пшеничная"
    assert flour.group is manager.groups[0]
    assert flour.unit is kilogram

    all_models = (
        manager.warehouses
        + manager.groups
        + manager.units
        + manager.items
    )
    codes = [model.unique_code for model in all_models]

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