from Src.Core.abstract_restore_handler import abstract_restore_handler
from Src.Core.exception import arguments_exception
from Src.Dtos.restoration_context_dto import restoration_context_dto
from Src.Dtos.tuple_reference_dto import tuple_reference_dto


class dict_restore(abstract_restore_handler):
    """Восстанавливает словарь с типизированными ключами и циклическими значениями."""

    # Имя типа и поля формата словаря.
    type_name = "dict"
    expected_fields = {"$id", "$type", "$items"}

    def validate(self, node: dict) -> None:
        """Проверяет массив пар ключ-значение."""
        super().validate(node)
        if not isinstance(node["$items"], list):
            raise arguments_exception("$items", "Ожидается массив")
        if any(not isinstance(pair, list) or len(pair) != 2 for pair in node["$items"]):
            raise arguments_exception("$items", "Ожидаются пары ключ-значение")

    def children(self, node: dict) -> list:
        """Возвращает ключи и значения для предварительного обхода."""
        return [value for pair in node["$items"] for value in pair]

    def allocate(self, node: dict) -> dict:
        """Создаёт пустой словарь до восстановления его содержимого."""
        return {}

    def restore(self, instance: dict, node: dict, reader) -> dict:
        """Восстанавливает пары и отклоняет повторный ключ."""
        for key, value in node["$items"]:
            key = reader.restore_value(key)
            if key in instance:
                raise arguments_exception("$items", "Повторный ключ словаря")
            instance[key] = reader.restore_value(value)
        return instance

    def resolve(self, instance: dict, context: restoration_context_dto) -> None:
        """Связывает отложенные ссылки на кортежи в значениях словаря."""
        for key, value in instance.items():
            if isinstance(value, tuple_reference_dto):
                instance[key] = context.objects[value.identifier]
