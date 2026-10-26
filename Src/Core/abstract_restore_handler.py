from abc import ABC, abstractmethod

from Src.Core.exception import arguments_exception
from Src.Dtos.restoration_context_dto import restoration_context_dto, tuple_reference_dto


class abstract_restore_handler(ABC):
    """Определяет проверку и восстановление узла одного типа."""

    # Имя поддерживаемого типа в формате графа.
    type_name: str
    # Обязательный набор полей узла этого типа.
    expected_fields: set[str]

    def validate(self, node: dict) -> None:
        """Проверяет общий набор метаданных и идентификатор определения."""
        if set(node) != self.expected_fields:
            raise arguments_exception("source", "Некорректные поля определения объекта")
        if "$id" in self.expected_fields:
            identifier = node["$id"]
            if not isinstance(identifier, str) or not identifier:
                raise arguments_exception("$id", "Ожидается непустой строковый ID")

    def children(self, node: dict) -> list:
        """Возвращает вложенные узлы для предварительной проверки ссылок."""
        return []

    def allocate(self, node: dict) -> object:
        """Создаёт экземпляр до заполнения ссылок; атомарным значениям не нужен."""
        return None

    @abstractmethod
    def restore(self, instance: object, node: dict, reader) -> object:
        """Заполняет ранее зарегистрированный экземпляр или создаёт атомарное значение."""
        pass

    def resolve(self, instance: object, context: restoration_context_dto) -> None:
        """Связывает отложенные ссылки на кортежи в полях объекта."""
        if hasattr(instance, "__dict__"):
            for name, value in vars(instance).items():
                if isinstance(value, tuple_reference_dto):
                    setattr(instance, name, context.objects[value.identifier])

    def check(self, instance: object, node: dict) -> None:
        """Проверяет итоговое состояние, когда весь граф уже собран."""
        pass
