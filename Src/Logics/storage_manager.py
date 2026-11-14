from threading import RLock
from typing import Iterable

from Src.Core.abstract_entity_repository import (
    abstract_entity_repository,
    validate_entity_type,
)
from Src.Core.abstract_manager import abstract_manager
from Src.Core.entity_conflict_exception import entity_conflict_exception
from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Core.validator import operation_exception, validator
from Src.Logics.initial_catalog import initial_catalog
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.recipe_model import recipe_model
from Src.Models.settings_model import settings_model
from Src.Models.unit_model import unit_model
from Src.Models.warehouse_model import warehouse_model


class storage_manager(abstract_manager, abstract_entity_repository):
    """Репозиторий доменных сущностей в памяти с единым поиском по коду."""

    __instance = None
    __initialization_lock = RLock()

    def __new__(cls, settings: settings_model):
        """Создаёт общий экземпляр менеджера."""
        with cls.__initialization_lock:
            if cls.__instance is None:
                cls.__instance = super().__new__(cls)
                cls.__instance.__initialized = False
            return cls.__instance

    def __init__(self, settings: settings_model) -> None:
        """Подготавливает хранилище один раз при первом создании."""
        with self.__initialization_lock:
            if self.__initialized:
                return

            validator.validate(settings, settings_model, field="settings")
            self.__settings = settings
            self.__models: dict[str, entity_model] = {}
            self.__incoming: dict[str, set[str]] = {}
            self.__lock = RLock()
            self._is_loaded = False
            self.convert()
            self.__initialized = True

    @classmethod
    def initialize_empty(cls, instance: "storage_manager") -> None:
        """Инициализирует отдельное хранилище без стартовых данных."""
        if type(instance) is not cls:
            raise arguments_exception("instance", "Ожидается экземпляр хранилища")
        settings = settings_model()
        settings.first_start = False
        instance.__initialized = False
        cls.__init__(instance, settings)

    @property
    def warehouses(self) -> tuple[warehouse_model, ...]:
        """Возвращает зарегистрированные склады."""
        return self.list(warehouse_model)

    @property
    def units(self) -> tuple[unit_model, ...]:
        """Возвращает зарегистрированные единицы измерения."""
        return self.list(unit_model)

    @property
    def items(self) -> tuple[item_model, ...]:
        """Возвращает зарегистрированную номенклатуру, включая состав рецептов."""
        return self.list(item_model)

    @property
    def groups(self) -> tuple[group_model, ...]:
        """Возвращает зарегистрированные группы."""
        return self.list(group_model)

    @property
    def recipes(self) -> tuple[recipe_model, ...]:
        """Возвращает самостоятельные и вложенные карты."""
        return self.list(recipe_model)

    def convert(self) -> bool:
        """Регистрирует стартовые модели один раз с учётом настроек."""
        with self.__lock:
            if self._is_loaded:
                return True

            if self.__settings.first_start:
                try:
                    self.register_models(initial_catalog())
                except arguments_exception as error:
                    raise operation_exception("Не удалось подготовить данные хранилища") from error

            self._is_loaded = True
            return True

    def list(self, entity_type: type[entity_model]) -> tuple[entity_model, ...]:
        """Возвращает снимок состава коллекции в порядке регистрации."""
        validate_entity_type(entity_type)
        with self.__lock:
            return tuple(model for model in self.__models.values() if isinstance(model, entity_type))

    def find(self, entity_type: type[entity_model], code: str) -> entity_model | None:
        """Находит зарегистрированный объект по типу и коду."""
        validate_entity_type(entity_type)
        validator.validate(code, str, field="code")
        with self.__lock:
            model = self.__models.get(code.strip())
            return model if isinstance(model, entity_type) else None

    def add(self, entity_type: type[entity_model], value: entity_model) -> None:
        """Регистрирует сущность, используя те же проверки, что и загрузка коллекций."""
        validate_entity_type(entity_type)
        validator.validate(value, entity_type)
        self.register_models((value,))

    def find_references(self, entity_type: type[entity_model], code: str) -> tuple[entity_model, ...]:
        """Находит владельцев входящих ссылок, включая строки и характеристики массы."""
        with self.__lock:
            model = self.find(entity_type, code)
            if model is None:
                return ()
            return tuple(self.__models[owner] for owner in self.__incoming.get(model.unique_code, ()))

    def delete(self, entity_type: type[entity_model], code: str) -> bool:
        """Удаляет сущность без входящих ссылок и снимает её исходящие связи."""
        with self.__lock:
            model = self.find(entity_type, code)
            if model is None:
                return False
            if self.find_references(entity_type, code):
                raise entity_conflict_exception("code", "На сущность ссылаются другие сущности")
            self.__remove_references(model.unique_code, self.__reference_codes(model))
            del self.__models[model.unique_code]
            model._set_registered(False)
            return True

    def update(
        self, entity_type: type[entity_model], code: str, fields: dict[str, object],
    ) -> entity_model | None:
        """Проверяет частичное изменение и сохраняет идентичность существующей модели."""
        with self.__lock:
            model = self.find(entity_type, code)
            if model is None:
                return None
            candidate = model.updated_copy(fields)
            old_code = model.unique_code
            new_code = candidate.unique_code
            if new_code != old_code:
                if self.find_references(entity_type, old_code):
                    raise entity_conflict_exception("unique_code", "На сущность ссылаются другие сущности")
                if new_code in self.__models:
                    raise entity_conflict_exception("unique_code", "Объект с таким кодом уже существует")

            new_targets = self.__validate_references({}, candidate, original=model)
            old_targets = self.__reference_codes(model)
            with model._apply_update(candidate):
                self.__validate_affected_models(old_code, model)

            self.__remove_references(old_code, old_targets)
            if new_code != old_code:
                del self.__models[old_code]
                self.__models[new_code] = model
            self.__add_references(new_code, new_targets)
            return model

    def __validate_affected_models(self, old_code: str, model: entity_model) -> None:
        """Проверяет изменённую модель и её зависимые сущности по индексу."""
        pending = [old_code]
        visited: set[str] = set()
        while pending:
            code = pending.pop()
            if code in visited:
                continue
            visited.add(code)
            affected = model if code == old_code else self.__models[code]
            affected.validate_state()
            pending.extend(self.__incoming.get(code, ()))

    def add_warehouse(self, value: warehouse_model) -> None:
        """Добавляет склад через общий репозиторий."""
        self.add(warehouse_model, value)

    def add_unit(self, value: unit_model) -> None:
        """Добавляет единицу через общий репозиторий."""
        self.add(unit_model, value)

    def add_group(self, value: group_model) -> None:
        """Добавляет группу через общий репозиторий."""
        self.add(group_model, value)

    def add_item(self, value: item_model) -> None:
        """Добавляет номенклатуру через общий репозиторий."""
        self.add(item_model, value)

    def register_models(self, values: Iterable[entity_model]) -> None:
        """Регистрирует пакет атомарно с учётом связей между его сущностями."""
        with self.__lock:
            pending: dict[str, entity_model] = {}
            for value in values:
                validator.validate(value, entity_model)
                self.__stage(pending, value)

            outgoing = {}
            for code, value in pending.items():
                outgoing[code] = self.__validate_references(pending, value)
                value.validate_state()
            self.__models.update(pending)
            for code, value in pending.items():
                self.__add_references(code, outgoing[code])
                value._set_registered(True)

    def __stage(self, pending: dict[str, entity_model], value: entity_model) -> None:
        """Отклоняет повторную регистрацию и конфликт кода между типами."""
        code = value.unique_code
        if code in pending or code in self.__models:
            raise entity_conflict_exception("unique_code", "Объект с таким кодом уже существует")
        if value.is_registered:
            raise entity_conflict_exception("value", "Сущность уже зарегистрирована в другом хранилище")
        pending[code] = value

    def __validate_references(
        self, pending: dict[str, entity_model], value: entity_model, *, original: entity_model | None = None,
    ) -> set[str]:
        """Проверяет регистрацию целей и возвращает их коды для индекса."""
        targets = set()
        for field, target in value.references():
            if target is value or target is original:
                continue
            validator.validate(target, entity_model, field=field)
            registered = pending.get(target.unique_code) or self.__models.get(target.unique_code)
            if registered is not target:
                raise arguments_exception(field, "Связанная сущность отсутствует в хранилище")
            targets.add(target.unique_code)
        return targets

    @staticmethod
    def __reference_codes(model: entity_model) -> set[str]:
        """Возвращает коды исходящих связей для удаления записей из индекса."""
        return {target.unique_code for _, target in model.references() if target is not model}

    def __add_references(self, owner: str, targets: set[str]) -> None:
        """Добавляет владельца к входящим ссылкам каждой цели."""
        for target in targets:
            self.__incoming.setdefault(target, set()).add(owner)

    def __remove_references(self, owner: str, targets: set[str]) -> None:
        """Снимает исходящие связи владельца и освобождает пустые записи индекса."""
        for target in targets:
            owners = self.__incoming[target]
            owners.remove(owner)
            if not owners:
                del self.__incoming[target]
