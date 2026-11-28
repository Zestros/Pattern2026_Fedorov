from abc import ABC, abstractmethod
from collections.abc import Callable

from Src.Dtos.operation_event_dto import operation_event_dto


class abstract_event_source(ABC):
    """Контракт подключения источника событий к издателю."""

    @abstractmethod
    def set_event_publisher(self, publish_event: Callable[[operation_event_dto], None]) -> None:
        """Подключает функцию публикации событий источника."""
