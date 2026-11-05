from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Src.Core.abstract_convertor import abstract_convertor


class abstract_convert_factory(ABC):
    """Определяет выбор конвертора для переданного значения."""

    @abstractmethod
    def create(self, source: object) -> abstract_convertor:
        """Возвращает конвертор, поддерживающий тип значения."""
        pass
