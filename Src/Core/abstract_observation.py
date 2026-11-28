from abc import ABC, abstractmethod

from Src.Dtos.operation_event_dto import operation_event_dto


class abstract_observation(ABC):
    """Общий контракт подписчика на события операций."""

    @abstractmethod
    def handler(self, event: operation_event_dto) -> None:
        """Обрабатывает событие, полученное от диспетчера."""
        pass
