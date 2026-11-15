from Src.Core.exception import arguments_exception
from Src.Dtos.restoration_context_dto import restoration_context_dto
from Src.Dtos.tuple_reference_dto import tuple_reference_dto
from Src.Logics.Restore.list_restore import list_restore


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
