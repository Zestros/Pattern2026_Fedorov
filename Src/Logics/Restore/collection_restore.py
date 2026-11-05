from Src.Core.abstract_restore_handler import abstract_restore_handler
from Src.Core.exception import arguments_exception
from Src.Dtos.restoration_context_dto import restoration_context_dto, tuple_reference_dto


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


class tuple_restore(list_restore):
    """Восстанавливает неизменяемый кортеж и обратные ссылки через его владельцев."""

    # Поля формата совпадают со списком, имя типа сохраняется отдельно.
    type_name = "tuple"

    def allocate(self, node: dict) -> tuple_reference_dto:
        """Регистрирует временную ссылку до создания окончательного кортежа."""
        return tuple_reference_dto(node["$id"])

    def restore(self, instance: object, node: dict, reader) -> tuple:
        """Создаёт кортеж после чтения детей и отклоняет невозможный прямой цикл."""
        values = [reader.restore_value(value) for value in node["$values"]]
        if any(isinstance(value, tuple_reference_dto) for value in values):
            raise arguments_exception("tuple", "Прямой цикл неизменяемых tuple невозможен")
        return tuple(values)

    def resolve(self, instance: tuple, context: restoration_context_dto) -> None:
        """Кортеж готов; обратные ссылки исправляются в изменяемых владельцах."""
        pass


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
