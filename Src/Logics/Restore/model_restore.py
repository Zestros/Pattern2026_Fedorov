from inspect import getattr_static

from Src.Core.abstract_model import abstract_model
from Src.Core.abstract_restore_handler import abstract_restore_handler
from Src.Core.exception import arguments_exception
from Src.Logics.storage_manager import storage_manager
from Src.Models.recipe_model import recipe_model
from Src.Models.settings_model import settings_model
from Src.Models.unit_model import unit_model


class model_restore(abstract_restore_handler):
    """Восстанавливает модель через конструктор и публичные изменяемые поля."""

    def __init__(self, model_type, constructor_fields: list[str]) -> None:
        """Задаёт класс модели и поля, передаваемые её конструктору."""
        self.model_type = model_type
        self.type_name = model_type.__name__
        self.constructor_fields = constructor_fields
        self.handled_fields = set(constructor_fields)
        self.expected_fields = {"$id", "$type", "$fields"}

    def validate(self, node: dict) -> None:
        """Проверяет, что состояние модели содержит публичные именованные поля."""
        super().validate(node)
        fields = node["$fields"]
        if not isinstance(fields, dict) or any(
            not isinstance(name, str) or name.startswith("_") for name in fields
        ):
            raise arguments_exception("$fields", "Ожидаются публичные именованные поля")

    def children(self, node: dict) -> list:
        """Возвращает значения свойств для предварительного обхода графа."""
        return list(node["$fields"].values())

    def allocate(self, node: dict) -> object:
        """Создаёт экземпляр без инициализации для регистрации обратных ссылок."""
        return self.model_type.__new__(self.model_type)

    def restore(self, instance: object, node: dict, reader) -> object:
        """Восстанавливает аргументы, выполняет конструктор и заполняет остальные поля."""
        fields = {name: reader.restore_value(value) for name, value in node["$fields"].items()}
        self.initialize(instance, fields)
        self.fill_fields(instance, fields)
        return instance

    def initialize(self, instance: object, fields: dict) -> None:
        """Передаёт зарегистрированный набор аргументов проверяемому конструктору."""
        arguments = {name: fields[name] for name in self.constructor_fields}
        self.model_type.__init__(instance, **arguments)

    def fill_fields(self, instance: object, fields: dict) -> None:
        """Сохраняет доменный код и дополнительные публичные поля без обхода свойств."""
        handled = self.handled_fields.copy()
        if isinstance(instance, abstract_model):
            instance.unique_code = fields["unique_code"]
            handled.add("unique_code")
        for name, value in fields.items():
            if name in handled:
                continue
            descriptor = getattr_static(type(instance), name, None)
            if isinstance(descriptor, property) and descriptor.fset is None:
                raise arguments_exception(name, "Неизвестное поле только для чтения")
            setattr(instance, name, value)


class unit_restore(model_restore):
    """Восстанавливает единицу и её самоссылку средствами конструктора модели."""

    def __init__(self) -> None:
        """Регистрирует аргументы конструктора единицы."""
        super().__init__(unit_model, ["name", "coefficient", "base_unit"])

    def initialize(self, instance: unit_model, fields: dict) -> None:
        """Распознаёт ссылку на создаваемый экземпляр перед вызовом конструктора."""
        base = fields["base_unit"]
        if base is None:
            raise arguments_exception("base_unit", "В графе база должна быть объектом или ссылкой")
        arguments = dict(fields)
        arguments["base_unit"] = None if base is instance else base
        super().initialize(instance, arguments)


class recipe_restore(model_restore):
    """Восстанавливает карту до её строк и проверяет пересчитанные массы."""

    def __init__(self) -> None:
        """Отделяет аргументы карты, её строки и вычисляемые свойства."""
        super().__init__(recipe_model, ["name", "mass_unit", "mass_coefficient"])
        self.computed_fields = {"gross_weight", "net_weight", "packaging_weight"}
        self.handled_fields.update(self.computed_fields | {"ingredients"})

    def restore(self, instance: recipe_model, node: dict, reader) -> recipe_model:
        """Создаёт пустую карту, затем добавляет строки через публичный метод."""
        source = node["$fields"]
        header = {name: reader.restore_value(source[name]) for name in self.constructor_fields}
        self.initialize(instance, header)
        instance.unique_code = source["unique_code"]
        fields = {name: reader.restore_value(value) for name, value in source.items()}
        for ingredient in fields["ingredients"]:
            instance.add_ingredient(ingredient)
        self.fill_fields(instance, fields)
        return instance

    def check(self, instance: recipe_model, node: dict) -> None:
        """Сверяет расчётные свойства только после заполнения всего графа."""
        fields = node["$fields"]
        for name in self.computed_fields & fields.keys():
            if getattr(instance, name) != fields[name]:
                raise arguments_exception(name, "Расчётное поле не соответствует восстановленной модели")


class settings_restore(model_restore):
    """Восстанавливает настройки с учётом необязательных начальных значений."""

    def __init__(self) -> None:
        """Регистрирует поля настроек, заполняемые через их свойства."""
        super().__init__(settings_model, [])
        self.handled_fields.update({"company", "boss_name", "account_name", "first_start", "response_format"})

    def initialize(self, instance: settings_model, fields: dict) -> None:
        """Применяет заданные значения, сохраняя допустимые пустые значения по умолчанию."""
        super().initialize(instance, fields)
        for name in ("company", "boss_name", "account_name"):
            if fields[name] not in (None, ""):
                setattr(instance, name, fields[name])
        instance.first_start = fields["first_start"]
        instance.response_format = fields["response_format"]


class storage_restore(model_restore):
    """Заполняет отдельное хранилище без замены действующего Singleton."""

    def __init__(self) -> None:
        """Регистрирует публичные коллекции хранилища."""
        super().__init__(storage_manager, [])
        self.handled_fields.update({"groups", "warehouses", "units", "items"})

    def allocate(self, node: dict) -> storage_manager:
        """Выделяет отдельный экземпляр без вызова Singleton-конструктора __new__."""
        return object.__new__(storage_manager)

    def initialize(self, instance: storage_manager, fields: dict) -> None:
        """Создаёт пустое хранилище и добавляет модели с проверкой его правил."""
        settings = settings_model()
        settings.first_start = False
        instance._storage_manager__initialized = False
        storage_manager.__init__(instance, settings)
        collections = {
            "groups": instance.add_group, "warehouses": instance.add_warehouse,
            "units": instance.add_unit, "items": instance.add_item,
        }
        for name, add in collections.items():
            for value in fields[name]:
                add(value)
