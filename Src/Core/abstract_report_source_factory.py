from abc import ABC, abstractmethod
from typing import Any

from Src.Core.abstract_report_source import abstract_report_source
from Src.Core.entity_type_enum import entity_type_enum


class abstract_report_source_factory(ABC):
    """Определяет выбор обработчика по типу сущности."""

    @abstractmethod
    def create(self, entity_type: entity_type_enum) -> abstract_report_source[Any]:
        """Возвращает обработчик; конкретный тип модели проверяется при build."""
        pass
