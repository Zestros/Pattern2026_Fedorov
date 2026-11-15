from Src.Core.abstract_restore_handler import abstract_restore_handler
from Src.Core.exception import arguments_exception
from Src.Dtos.restoration_context_dto import restoration_context_dto
from Src.Dtos.tuple_reference_dto import tuple_reference_dto


class list_restore(abstract_restore_handler):
    """Восстанавливает изменяемый список с общими и циклическими ссылками."""

    # Имя типа и поля формата списка.
    type_name = "list"
    expected_fields = {"$id", "$type", "$values"}

    def validate(self, node: dict) -> None:
        """Проверяет метаданные и массив элементов."""
        super().validate(node)
        if not isinstance(node["$values"], list):
            raise arguments_exception("$values", "Ожидается массив")

    def children(self, node: dict) -> list:
        """Возвращает элементы списка для обхода графа."""
        return node["$values"]

    def allocate(self, node: dict) -> list:
        """Создаёт пустой список до чтения его элементов."""
        return []

    def restore(self, instance: list, node: dict, reader) -> list:
        """Заполняет тот же экземпляр списка восстановленными элементами."""
        instance.extend(reader.restore_value(value) for value in node["$values"])
        return instance

    def resolve(self, instance: list, context: restoration_context_dto) -> None:
        """Заменяет отложенные ссылки на кортежи в элементах списка."""
        for index, value in enumerate(instance):
            if isinstance(value, tuple_reference_dto):
                instance[index] = context.objects[value.identifier]
