from Src.Core.abstract_report_factory import abstract_report_factory
from Src.Core.abstract_report_source_factory import abstract_report_source_factory
from Src.Core.entity_type_enum import entity_type_enum
from Src.Core.report_type_enum import report_type_enum
from Src.Dtos.report_result_dto import report_result_dto
from Src.Dtos.report_data_dto import report_data_dto
from Src.Logics.storage_manager import storage_manager


class report_not_found_exception(Exception):
    """Сущность для отчёта отсутствует в хранилище."""


class report_service:
    """Связывает поиск, подготовку данных и форматирование без HTTP-зависимостей."""

    def __init__(self, storage: storage_manager,
                 sources: abstract_report_source_factory,
                 reports: abstract_report_factory) -> None:
        """Получает зависимости для формирования отчётов."""
        self.__storage = storage
        self.__sources = sources
        self.__reports = reports

    def __prepare(self, entity_type: entity_type_enum, code: str) -> report_data_dto:
        """Находит сущность и подготавливает её данные."""
        entity = self.__storage.find(entity_type, code)
        if entity is None:
            raise report_not_found_exception("Сущность не найдена")
        return self.__sources.create(entity_type).build(entity)

    def build(self, entity_type: entity_type_enum, code: str,
              response_format: report_type_enum) -> report_result_dto:
        """Создаёт отчёт в явно указанном формате."""
        report = self.__reports.create(response_format)
        return report.build(self.__prepare(entity_type, code))

    def build_default(self, entity_type: entity_type_enum, code: str) -> report_result_dto:
        """Создаёт отчёт в формате из настроек фабрики."""
        report = self.__reports.create_default()
        return report.build(self.__prepare(entity_type, code))
