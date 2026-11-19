"""Интеграционные проверки репозитория, маппинга и самостоятельных графов."""
import pytest
from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Dtos.entity_dto import entity_dto
from Src.Logics.dto_mapping import model_mapping, mapping_registry, dto_mapper
from Src.Logics.storage_repository import storage_repository
from Src.Logics.resource_catalog import resource_definition, resource_catalog
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.unit_model import unit_model
from Src.Models.recipe_model import recipe_model


class node_model(entity_model):
    """Тестовая сущность с допустимой самоссылкой, не являющаяся единицей."""
    def __init__(self, name: str, parent: entity_model | None = None) -> None:
        """Создаёт узел с необязательной связью на родителя."""
        super().__init__()
        self.name = name
        self.__parent = parent

    @property
    def parent(self) -> entity_model | None:
        """Возвращает родителя, включая допустимую ссылку на себя."""
        return self.__parent

    @parent.setter
    def parent(self, value: entity_model | None) -> None:
        """Устанавливает связь до регистрации узла."""
        self.__parent = value


class dependent_model(node_model):
    """Тестовая сущность, запрещающая изменение имени связанной группы."""
    def validate_state(self) -> None:
        """Проверяет правило, зависящее от состояния другого объекта."""
        if self.parent.name != "Исходное имя":
            raise arguments_exception("parent", "Имя связанной группы нельзя изменить")


class node_dto(entity_dto):
    """Контракт узла с внешней ссылкой по коду."""
    _references = {"parent": "node"}
    parent: str | None = None


def test_preserved_self_reference_change_non_unit_model():
    """<summary>Общий Mapper сохраняет самоссылку обычного узла при изменении
    имени и не применяет к нему специальное правило единицы измерения.</summary>"""
    # Подготовка
    repository = storage_repository()
    registry = mapping_registry((model_mapping(node_dto, node_model),))
    resources = resource_catalog(registry, (resource_definition("node", node_dto),))
    mapper = dto_mapper(registry, repository, resources)
    original = node_model("Узел")
    original.parent = original
    repository.add(node_model, original)
    patch = node_dto(name="Новое имя")

    # Действие
    changed = repository.change(node_model, original.unique_code,
                                lambda current: mapper.to_model(patch, current))

    # Проверка
    assert changed is original
    assert changed.parent is original
    assert changed.name == "Новое имя"


def test_independent_catalogs_add_same_code_different_repositories():
    """<summary>Два репозитория могут хранить разные объекты с одним кодом;
    состояние и регистрация одного каталога не влияют на другой.</summary>"""
    # Подготовка
    first, second = storage_repository(), storage_repository()
    left, right = group_model("Первая"), group_model("Вторая")
    left.unique_code = right.unique_code = "shared-code"

    # Действие
    first.add(group_model, left)
    second.add(group_model, right)
    first.delete(group_model, left.unique_code)

    # Проверка
    assert first.find(group_model, "shared-code") is None
    assert second.find(group_model, "shared-code") is right
    assert not left.is_registered
    assert right.is_registered


def test_unchanged_catalog_register_models_invalid_batch():
    """<summary>Пакет с конфликтом кодов в новой зависимости отклоняется целиком:
    ранее подготовленные объекты не публикуются и не помечаются зарегистрированными.</summary>"""
    # Подготовка
    repository = storage_repository()
    group = group_model("Группа")
    missing_unit = unit_model("Единица")
    missing_unit.unique_code = group.unique_code
    item = item_model("Товар", "Полное имя", group, missing_unit)

    # Действие
    with pytest.raises(arguments_exception):
        repository.register_models((group, item))

    # Проверка
    assert repository.list(entity_model) == ()
    assert not group.is_registered
    assert not item.is_registered
    assert repository.find_references(group_model, group.unique_code) == ()


def test_unchanged_catalog_change_rejected_dependent_model():
    """<summary>Ошибка проверки зависимого объекта откатывает имя и сохраняет
    идентичность изменяемой сущности и индекс входящих ссылок.</summary>"""
    # Подготовка
    repository = storage_repository()
    original = group_model("Исходное имя")
    repository.add(group_model, original)
    dependent = dependent_model("Зависимая сущность", original)
    repository.add(dependent_model, dependent)
    candidate = group_model("Новое имя")
    candidate.unique_code = original.unique_code

    # Действие
    with pytest.raises(arguments_exception):
        repository.change(group_model, original.unique_code, lambda current: candidate)

    # Проверка
    assert repository.find(group_model, original.unique_code) is original
    assert original.name == "Исходное имя"
    assert original.is_registered
    assert repository.find_references(group_model, original.unique_code) == (dependent,)


def test_registered_graph_add_mutual_cycle():
    """<summary>Регистрация одного узла сохраняет весь допустимый цикл
    ровно один раз и индексирует обе входящие связи.</summary>"""
    # Подготовка
    repository = storage_repository()
    first, second = node_model("Первый"), node_model("Второй")
    first.parent, second.parent = second, first

    # Действие
    repository.add(node_model, first)

    # Проверка
    assert len(repository.list(node_model)) == 2
    assert repository.find(node_model, second.unique_code) is second
    assert repository.find_references(node_model, first.unique_code) == (second,)
    assert repository.find_references(node_model, second.unique_code) == (first,)


def test_released_reference_delete_shared_dependency_owners():
    """<summary>Общая зависимость регистрируется один раз; удаление каждого
    владельца снимает его ссылку и позволяет затем удалить зависимость.</summary>"""
    # Подготовка
    repository = storage_repository()
    group = group_model("Общая группа")
    first, second = node_model("Первый", group), node_model("Второй", group)

    # Действие
    repository.add(node_model, first)
    repository.add(node_model, second)
    owners = repository.find_references(group_model, group.unique_code)
    repository.delete(node_model, first.unique_code)
    remaining = repository.find_references(group_model, group.unique_code)
    repository.delete(node_model, second.unique_code)
    deleted = repository.delete(group_model, group.unique_code)

    # Проверка
    assert {id(owner) for owner in owners} == {id(first), id(second)}
    assert remaining == (second,)
    assert deleted
    assert repository.list(entity_model) == ()


def test_registered_dependencies_change_new_related_object():
    """<summary>Изменение регистрирует новую зависимость, сохраняет экземпляр
    владельца и переносит входящую ссылку с прежнего объекта на новый.</summary>"""
    # Подготовка
    repository = storage_repository()
    previous, new = group_model("Прежняя"), group_model("Новая")
    original = node_model("Владелец", previous)
    repository.add(node_model, original)
    candidate = node_model(original.name, new)
    candidate.unique_code = original.unique_code

    # Действие
    changed = repository.change(node_model, original.unique_code, lambda current: candidate)

    # Проверка
    assert changed is original
    assert changed.parent is new
    assert repository.find(group_model, new.unique_code) is new
    assert repository.find_references(group_model, new.unique_code) == (original,)
    assert repository.find_references(group_model, previous.unique_code) == ()


def test_unchanged_graph_change_invalid_new_dependency():
    """<summary>Если новое связанное состояние нарушает правило модели,
    кандидат откатывается, а подготовленная зависимость не публикуется.</summary>"""
    # Подготовка
    repository = storage_repository()
    previous = group_model("Исходное имя")
    original = dependent_model("Владелец", previous)
    repository.add(dependent_model, original)
    new = group_model("Недопустимое имя")
    candidate = dependent_model(original.name, new)
    candidate.unique_code = original.unique_code

    # Действие
    with pytest.raises(arguments_exception):
        repository.change(dependent_model, original.unique_code, lambda current: candidate)

    # Проверка
    assert original.parent is previous
    assert repository.find(group_model, new.unique_code) is None
    assert not new.is_registered
    assert repository.find_references(group_model, previous.unique_code) == (original,)


def test_rejected_dependency_add_object_owned_by_other_repository():
    """<summary>Автоматическая регистрация не присваивает объект чужого
    репозитория и не публикует ссылающийся на него новый корень.</summary>"""
    # Подготовка
    first, second = storage_repository(), storage_repository()
    group = group_model("Чужая группа")
    first.add(group_model, group)
    node = node_model("Владелец", group)

    # Действие
    with pytest.raises(arguments_exception):
        second.add(node_model, node)

    # Проверка
    assert second.list(entity_model) == ()
    assert not node.is_registered
    assert first.find(group_model, group.unique_code) is group


def test_registered_dependencies_add_recipe_ingredient_collection():
    """<summary>Регистрация одной карты обходит коллекцию ингредиентов,
    сохраняет продукт и его справочники, переиспользуя общую единицу массы.</summary>"""
    # Подготовка
    repository = storage_repository()
    group, unit = group_model("Группа"), unit_model("Грамм")
    item = item_model("Продукт", "Продукт для карты", group, unit)
    recipe = recipe_model("Карта", unit)
    recipe.add_ingredient(item, 2)

    # Действие
    repository.add(recipe_model, recipe)

    # Проверка
    assert len(repository.list(entity_model)) == 4
    assert repository.find(item_model, item.unique_code) is item
    assert repository.find(group_model, group.unique_code) is group
    assert repository.find(unit_model, unit.unique_code) is unit
    assert recipe.ingredients[0].item is item
    assert {id(owner) for owner in repository.find_references(unit_model, unit.unique_code)} == {id(recipe), id(item)}
