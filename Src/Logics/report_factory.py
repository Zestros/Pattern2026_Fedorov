from Src.Core.abstract_report_factory import abstract_report_factory
from Src.Core.abstract_report import abstract_report
from Src.Core.report_type_enum import report_type_enum
from Src.Core.exception import arguments_exception
from Src.Core.validator import validator
from Src.Logics.text_report import text_report


class report_factory(abstract_report_factory):
    """Создаёт отчёт указанного типа."""

    def __init__(self) -> None:
        """Регистрирует поддерживаемые классы отчётов."""
        self.__mapping: dict[
            report_type_enum, type[abstract_report]
        ] = {
            report_type_enum.TXT: text_report,
        }

    def create(self, report_type: report_type_enum) -> abstract_report:
        """Возвращает экземпляр отчёта или отклоняет неизвестный тип."""
        validator.validate(
            report_type,
            report_type_enum,
            field="report_type",
        )

        if report_type not in self.__mapping:
            raise arguments_exception(
                "report_type",
                f"Тип отчёта {report_type} не реализован",
            )

        return self.__mapping[report_type]()
