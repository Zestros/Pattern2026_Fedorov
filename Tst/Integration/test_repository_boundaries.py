"""Интеграционные проверки репозитория, маппинга и самостоятельных графов."""
import pytest
from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Dtos.entity_dto import entity_dto
from Src.Logics.dto_mapping import model_mapping, mapping_registry, dto_mapper
from Src.Logics.entity_repository import entity_repository
from Src.Logics.resource_catalog import resource_definition, resource_catalog
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.unit_model import unit_model


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
    repository = entity_repository()
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
    first, second = entity_repository(), entity_repository()
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
    """<summary>Пакет с незарегистрированной связью отклоняется целиком:
    ранее подготовленные объекты не публикуются и не помечаются зарегистрированными.</summary>"""
    # Подготовка
    repository = entity_repository()
    group = group_model("Группа")
    missing_unit = unit_model("Единица")
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
    repository = entity_repository()
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
