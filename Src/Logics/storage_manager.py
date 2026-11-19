from threading import RLock
from collections.abc import Iterable, Callable

from Src.Core.abstract_entity_repository import (
    abstract_entity_repository,
)
from Src.Core.abstract_manager import abstract_manager
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


from Src.Logics.entity_repository import entity_repository


class storage_manager(abstract_manager, abstract_entity_repository):
    """Фасад загрузки каталога; операции хранения делегирует репозиторию."""

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
            self.__repository = entity_repository()
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
        with self.__initialization_lock:
            if self._is_loaded:
                return True

            if self.__settings.first_start:
                try:
                    self.register_models(initial_catalog())
                except arguments_exception as error:
                    raise operation_exception("Не удалось подготовить данные хранилища") from error

            self._is_loaded = True
            return True

    def get_repository(self) -> entity_repository:
        """Возвращает репозиторий для подключения прикладных сценариев."""
        return self.__repository

    def list(self, entity_type: type[entity_model]):
        """Возвращает сущности типа через репозиторий."""
        return self.__repository.list(entity_type)

    def find(self, entity_type: type[entity_model], code: str):
        """Находит сущность через репозиторий."""
        return self.__repository.find(entity_type, code)

    def add(self, entity_type: type[entity_model], value: entity_model):
        """Передаёт регистрацию сущности репозиторию."""
        return self.__repository.add(entity_type, value)

    def find_references(self, entity_type: type[entity_model], code: str):
        """Получает владельцев ссылок через репозиторий."""
        return self.__repository.find_references(entity_type, code)

    def delete(self, entity_type: type[entity_model], code: str):
        """Передаёт удаление репозиторию."""
        return self.__repository.delete(entity_type, code)

    def update(self, entity_type: type[entity_model], code: str, fields: dict):
        """Сохраняет совместимость старых вызовов обновления."""
        return self.__repository.update(entity_type, code, fields)

    def change(self, entity_type: type[entity_model], code: str, prepare: Callable):
        """Передаёт атомарное изменение репозиторию."""
        return self.__repository.change(entity_type, code, prepare)

    def register_models(self, values: Iterable[entity_model]):
        """Передаёт пакетную регистрацию репозиторию."""
        return self.__repository.register_models(values)

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
