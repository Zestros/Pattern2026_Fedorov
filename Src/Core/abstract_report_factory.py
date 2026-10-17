from abc import ABC, abstractmethod

from Src.Core.abstract_report import abstract_report
from Src.Core.report_type_enum import report_type_enum


class abstract_report_factory(ABC):
    """Определяет создание построителей отчёта."""

    @abstractmethod
    def create(self, report_type: report_type_enum) -> abstract_report:
        """Создаёт построитель указанного формата."""
        pass

    @abstractmethod
    def create_default(self) -> abstract_report:
        """Создаёт построитель формата из настроек."""
        pass
