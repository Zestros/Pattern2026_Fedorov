from Src.Core.abstract_manager import abstract_manager
from Src.Core.exception import arguments_exception
from Src.Core.validator import operation_exception
from Src.Models.settings_model import settings_model
from Src.Models.warehouse_model import warehouse_model
from Src.Models.unit_model import unit_model
from Src.Models.item_model import item_model
from Src.Models.group_model import group_model


class storage_manager(abstract_manager):
    """Хранит доменные модели в единственном экземпляре менеджера."""

    # Единственный экземпляр менеджера.
    __instance = None

    def __new__(cls, settings: settings_model):
        """Создаёт менеджер один раз."""
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.__initialized = False

        return cls.__instance

    def __init__(self, settings: settings_model) -> None:
        """Подготавливает хранилище при первом создании."""
        if self.__initialized:
            return

        if not isinstance(settings, settings_model):
            raise arguments_exception(
                "settings",
                "Ожидается модель настроек",
            )

        self.__settings = settings
        self.__warehouses: list[warehouse_model] = []
        self.__units: list[unit_model] = []
        self.__items: list[item_model] = []
        self.__groups: list[group_model] = []
        self._is_loaded = False

        self.convert()
        self.__initialized = True

    @property
    def warehouses(self) -> tuple[warehouse_model, ...]:
        """Возвращает склады без возможности менять состав коллекции."""
        return tuple(self.__warehouses)

    @property
    def units(self) -> tuple[unit_model, ...]:
        """Возвращает единицы измерения."""
        return tuple(self.__units)

    @property
    def items(self) -> tuple[item_model, ...]:
        """Возвращает номенклатуру."""
        return tuple(self.__items)

    @property
    def groups(self) -> tuple[group_model, ...]:
        """Возвращает группы."""
        return tuple(self.__groups)

    def convert(self) -> bool:
        """Подготавливает данные один раз с учётом первого старта."""
        if self._is_loaded:
            return True

        try:
            warehouses = []
            units = []
            items = []
            groups = []

            if self.__settings.first_start:
                group = group_model("Бакалея")

                gram = unit_model("грамм")
                kilogram = unit_model("килограмм", 1000, gram)

                warehouse = warehouse_model("Основной склад")

                flour = item_model(
                    "Мука",
                    "Мука пшеничная",
                    group,
                    kilogram,
                )

                groups.append(group)
                units.extend([gram, kilogram])
                warehouses.append(warehouse)
                items.append(flour)

            self.__warehouses = warehouses
            self.__units = units
            self.__items = items
            self.__groups = groups
            self._is_loaded = True

            return True
        except Exception as error:
            raise operation_exception(
                "Не удалось подготовить данные хранилища"
            )
        
    def __add_model(self, value, expected_type, collection) -> None:
        """Проверяет тип и уникальность кода перед добавлением."""
        if not isinstance(value, expected_type):
            raise arguments_exception(
                "value",
                f"Ожидается модель {expected_type.__name__}",
            )

        collections = (
            self.__warehouses,
            self.__units,
            self.__items,
            self.__groups,
        )

        for models in collections:
            for model in models:
                if model.unique_code == value.unique_code:
                    raise arguments_exception(
                        "unique_code",
                        "Объект с таким кодом уже существует",
                    )

        collection.append(value)

    def add_warehouse(self, value: warehouse_model) -> None:
        """Добавляет уникальный склад."""
        self.__add_model(value, warehouse_model, self.__warehouses)

    def add_unit(self, value: unit_model) -> None:
        """Добавляет уникальную единицу с зарегистрированной базой."""
        if isinstance(value, unit_model):
            if value.base_unit is not value and not any(
                unit is value.base_unit for unit in self.__units
            ):
                raise arguments_exception(
                    "base_unit",
                    "Базовая единица отсутствует в хранилище",
                )

        self.__add_model(value, unit_model, self.__units)

    def add_group(self, value: group_model) -> None:
        """Добавляет уникальную группу."""
        self.__add_model(value, group_model, self.__groups)

    def add_item(self, value: item_model) -> None:
        """Добавляет номенклатуру с зарегистрированной группой и единицей."""
        if isinstance(value, item_model):
            if not any(group is value.group for group in self.__groups):
                raise arguments_exception(
                    "group",
                    "Группа отсутствует в хранилище",
                )

            if not any(unit is value.unit for unit in self.__units):
                raise arguments_exception(
                    "unit",
                    "Единица измерения отсутствует в хранилище",
                )

        self.__add_model(value, item_model, self.__items)




    