from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from Src.Core.entity_model import entity_model
from Src.Dtos.report_data_dto import report_data_dto


source_type = TypeVar("source_type", bound=entity_model)


class abstract_report_source(ABC, Generic[source_type]):
    """Определяет подготовку данных конкретного типа сущности."""

    @abstractmethod
    def build(self, source: source_type) -> report_data_dto:
        """Возвращает поля и таблицу переданной сущности."""
        pass
