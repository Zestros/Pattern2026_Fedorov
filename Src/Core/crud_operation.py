from enum import StrEnum


class crud_operation(StrEnum):
    """Задаёт имена операций со справочниками для журнала."""

    # Создание сущности.
    CREATE = "create"
    # Чтение сущности по коду.
    GET = "get"
    # Чтение списка сущностей.
    LIST = "list"
    # Поиск сущностей по критериям.
    SEARCH = "search"
    # Изменение сущности.
    CHANGE = "change"
    # Удаление сущности.
    DELETE = "delete"
