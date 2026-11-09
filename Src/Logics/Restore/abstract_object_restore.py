from abc import abstractmethod

from Src.Core.abstract_restore_handler import abstract_restore_handler
from Src.Core.exception import arguments_exception


class abstract_object_restore(abstract_restore_handler):
    """Читает узел объекта и передаёт восстановленные поля обработчику."""

    # Формат узла с именованными полями.
    expected_fields = {"$id", "$type", "$fields"}

    def validate(self, node: dict) -> None:
        """Проверяет метаданные и публичные имена полей."""
        super().validate(node)
        fields = node["$fields"]
        if not isinstance(fields, dict) or any(
            not isinstance(name, str) or name.startswith("_") for name in fields
        ):
            raise arguments_exception("$fields", "Ожидаются публичные именованные поля")

    def children(self, node: dict) -> list:
        """Возвращает значения полей для предварительного обхода графа."""
        return list(node["$fields"].values())

    def restore(self, instance: object, node: dict, reader) -> object:
        """Читает значения и передаёт их уже выделенному экземпляру."""
        fields = {name: reader.restore_value(value) for name, value in node["$fields"].items()}
        return self.restore_fields(instance, fields)

    @abstractmethod
    def restore_fields(self, instance: object, fields: dict[str, object]) -> object:
        """Инициализирует экземпляр из восстановленных значений Python."""
        pass
