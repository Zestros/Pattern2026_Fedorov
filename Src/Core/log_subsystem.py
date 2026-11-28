from enum import StrEnum


class log_subsystem(StrEnum):
    """Определяет подсистему, в которой произошла операция."""

    # Операции со справочниками.
    CRUD = "CRUD"
    # Обработка HTTP-запросов.
    HTTP = "HTTP"
    # Складские операции.
    STORAGE = "STORAGE"
    # Загрузка и изменение настроек приложения.
    SETTINGS = "SETTINGS"
