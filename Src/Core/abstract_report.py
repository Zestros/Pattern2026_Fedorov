from Src.Core.report_result_dto import report_result_dto
from abc import ABC, abstractmethod

class abstract_report(ABC):
    """Абстрактная класс для формирования отчета"""

    @abstractmethod
    def build(self) -> report_result_dto:
        """Метод создания отчета"""
        pass