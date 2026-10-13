from Src.Core.abstract_report import abstract_report
from abc import ABC

class abstract_report_factory(ABC):

    def create(report_type, report_type_enum) -> abstract_report:
        pass