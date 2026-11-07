from Src.Logics.Restore.model_restore import model_restore
from Src.Logics.storage_manager import storage_manager
from Src.Models.settings_model import settings_model


class storage_restore(model_restore):
    """Заполняет отдельное хранилище без замены действующего Singleton."""

    def __init__(self) -> None:
        """Регистрирует публичные коллекции хранилища."""
        super().__init__(storage_manager)
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
