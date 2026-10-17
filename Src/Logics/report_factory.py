from Src.Models.settings_model import settings_model
from Src.Logics.csv_report import csv_report
from Src.Logics.markdown_report import markdown_report
from Src.Logics.xml_report import xml_report
from Src.Logics.html_report import html_report
from Src.Core.abstract_report_factory import abstract_report_factory
from Src.Core.abstract_report import abstract_report
from Src.Core.report_type_enum import report_type_enum
from Src.Core.exception import arguments_exception
from Src.Core.validator import validator
from Src.Logics.text_report import text_report


class report_factory(abstract_report_factory):
    """Создаёт отчёт указанного типа."""

    def __init__(self, settings: settings_model) -> None:
        """Регистрирует поддерживаемые классы отчётов."""
        validator.validate(settings, settings_model, field="settings")
        self.__settings = settings
        self.__mapping: dict[
            report_type_enum, type[abstract_report]
        ] = {
            report_type_enum.TXT: text_report,
            report_type_enum.CSV: csv_report,
            report_type_enum.MARKDOWN: markdown_report,
            report_type_enum.XML: xml_report,
            report_type_enum.HTML: html_report,

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


    def create_default(self) -> abstract_report:
        """Создаёт построитель по текущему значению сохранённых настроек."""
        return self.create(self.__settings.response_format)
