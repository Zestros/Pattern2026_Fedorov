from Src.Core.exception import arguments_exception
from Src.Logics.Restore.abstract_object_restore import abstract_object_restore
from Src.Logics.collect_entity_graph import collect_entity_graph
from Src.Logics.storage_manager import storage_manager
from Src.Models.group_model import group_model
from Src.Models.item_model import item_model
from Src.Models.recipe_model import recipe_model
from Src.Models.unit_model import unit_model
from Src.Models.warehouse_model import warehouse_model


class storage_restore(abstract_object_restore):
    """Заполняет отдельное хранилище с проверкой правил менеджера."""

    # Имя инфраструктурного узла в JSON.
    type_name = storage_manager.__name__
    collection_types = {
        "groups": group_model,
        "warehouses": warehouse_model,
        "units": unit_model,
        "items": item_model,
        "recipes": recipe_model,
    }

    def validate(self, node: dict) -> None:
        """Проверяет контракт коллекций до создания хранилища."""
        super().validate(node)
        fields = set(node["$fields"])
        if fields not in (self.collection_types.keys(), self.collection_types.keys() - {"recipes"}):
            raise arguments_exception("$fields", "Некорректный набор коллекций хранилища")

    def allocate(self, node: dict) -> storage_manager:
        """Выделяет отдельный экземпляр без вызова Singleton-конструктора __new__."""
        return object.__new__(storage_manager)

    def restore_fields(
        self, instance: storage_manager, fields: dict[str, object],
    ) -> storage_manager:
        """Регистрирует связанные коллекции независимо от их порядка в JSON."""
        storage_manager.initialize_empty(instance)
        models = []
        for name, model_type in self.collection_types.items():
            values = fields.get(name, ())
            if not isinstance(values, (list, tuple)):
                raise arguments_exception(name, "Ожидается коллекция моделей")
            for value in values:
                if not isinstance(value, model_type):
                    raise arguments_exception(name, f"Ожидается модель {model_type.__name__}")
                models.append(value)
        if "recipes" not in fields:
            # Старые снимки хранили часть номенклатуры и все карты внутри рецептов.
            explicit = {id(model) for model in models}
            models = [
                model for model in collect_entity_graph(models)
                if id(model) in explicit or isinstance(model, (item_model, recipe_model))
            ]
        instance.register_models(models)
        return instance
