from Src.Core.exception import arguments_exception
from Src.Logics.Restore.abstract_object_restore import abstract_object_restore
from Src.Logics.storage_manager import storage_manager


class storage_restore(abstract_object_restore):
    """Заполняет отдельное хранилище с проверкой правил менеджера."""

    # Имя инфраструктурного узла в JSON.
    type_name = storage_manager.__name__

    def validate(self, node: dict) -> None:
        """Проверяет контракт коллекций до создания хранилища."""
        super().validate(node)
        if set(node["$fields"]) != {"groups", "warehouses", "units", "items"}:
            raise arguments_exception("$fields", "Ожидаются четыре коллекции хранилища")

    def allocate(self, node: dict) -> storage_manager:
        """Выделяет отдельный экземпляр без вызова Singleton-конструктора __new__."""
        return object.__new__(storage_manager)

    def restore_fields(
        self, instance: storage_manager, fields: dict[str, object],
    ) -> storage_manager:
        """Инициализирует пустое хранилище и добавляет восстановленные модели."""
        storage_manager.initialize_empty(instance)
        collections = {
            "groups": instance.add_group, "warehouses": instance.add_warehouse,
            "units": instance.add_unit, "items": instance.add_item,
        }
        for name, add in collections.items():
            for value in fields[name]:
                add(value)
        return instance
