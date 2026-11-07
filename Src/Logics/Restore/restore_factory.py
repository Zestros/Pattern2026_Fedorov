from threading import Lock

from Src.Core.abstract_restore_handler import abstract_restore_handler
from Src.Core.exception import arguments_exception
from Src.Logics.Restore.model_restore import model_restore
from Src.Logics.Restore.restore_registration import register_restore_handlers


class restore_factory:
    """Хранит общий реестр и выбирает обработчик по $type."""

    # Один полностью настроенный экземпляр фабрики для всех операций.
    __instance = None
    __lock = Lock()

    def __new__(cls) -> "restore_factory":
        """Создаёт и настраивает фабрику при первом обращении."""
        with cls.__lock:
            if cls.__instance is None:
                instance = super().__new__(cls)
                instance.__handlers = {}
                register_restore_handlers(instance)
                cls.__instance = instance
            return cls.__instance

    def add_model(self, model_type: type) -> None:
        """Регистрирует модель с общим обработчиком."""
        self.add_handler(model_restore(model_type))

    def add_handler(self, handler: abstract_restore_handler) -> None:
        """Регистрирует обработчик по имени типа в JSON."""
        self.__handlers[handler.type_name] = handler

    def create(self, node: dict) -> abstract_restore_handler:
        """Возвращает обработчик известного типа и отклоняет неизвестное имя."""
        type_name = node.get("$type")
        if not isinstance(type_name, str):
            raise arguments_exception("$type", "Не указан тип значения")
        if type_name not in self.__handlers:
            raise arguments_exception("$type", f"Неизвестный тип: {type_name}")
        return self.__handlers[type_name]
