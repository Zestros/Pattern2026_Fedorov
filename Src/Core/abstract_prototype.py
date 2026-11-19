from abc import ABC, abstractmethod


class abstract_prototype(ABC):
    """Контракт клонирования коллекции."""

    @abstractmethod
    def clone(self):
        """Возвращает новый экземпляр с результатом отбора."""
