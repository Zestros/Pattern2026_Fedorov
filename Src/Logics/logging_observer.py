from contextlib import suppress
import sys

from Src.Core.abstract_observation import abstract_observation
from Src.Dtos.operation_event_dto import operation_event_dto
from Src.Logics.operation_logger import operation_logger


class logging_observer(abstract_observation):
    """Передаёт события операций в журнал приложения."""

    def __init__(self, logger: operation_logger) -> None:
        """Получает журнал, который будет записывать события."""
        self.__logger = logger

    def handler(self, event: operation_event_dto) -> None:
        """Записывает событие и отдельно сообщает об ошибке вывода."""
        try:
            self.__logger.write(event)
        except (OSError, ValueError) as error:
            with suppress(OSError, ValueError):
                print(f"Не удалось записать событие {event.subsystem}/{event.operation}: {error}", file=sys.stderr)
