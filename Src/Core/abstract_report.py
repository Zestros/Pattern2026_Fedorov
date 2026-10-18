from abc import ABC, abstractmethod

from Src.Dtos.report_result_dto import report_result_dto
from Src.Dtos.report_data_dto import report_data_dto


class abstract_report(ABC):
    """Определяет преобразование подготовленных данных в выбранный формат."""

    @abstractmethod
    def build(self, data: report_data_dto) -> report_result_dto:
        """Формирует результат из полей и таблицы отчёта."""
        pass
