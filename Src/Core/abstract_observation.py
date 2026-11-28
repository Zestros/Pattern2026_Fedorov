from abc import ABC, abstractmethod


class abstract_observation(ABC):
    """Элемент наблюдения"""

    @abstractmethod
    def handler(self, event_types: str, params: object) -> None:
        """Выполнить обработку события"""
        pass