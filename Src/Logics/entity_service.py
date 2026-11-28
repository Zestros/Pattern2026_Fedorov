from collections.abc import Callable, Generator, Iterable
from contextlib import contextmanager

from Src.Core.abstract_dto import abstract_dto
from Src.Core.abstract_entity_repository import abstract_entity_repository
from Src.Core.abstract_event_source import abstract_event_source
from Src.Core.crud_operation import crud_operation
from Src.Core.entity_conflict_exception import entity_conflict_exception
from Src.Core.entity_model import entity_model
from Src.Core.event_phase import event_phase
from Src.Core.exception import arguments_exception
from Src.Core.log_subsystem import log_subsystem
from Src.Dtos.entity_dto import entity_summary_dto
from Src.Dtos.filter_dto import filter_dto
from Src.Dtos.operation_event_dto import operation_event_dto
from Src.Logics.dto_mapping import dto_mapper
from Src.Logics.prototype import prototype
from Src.Logics.resource_catalog import resource_catalog


class entity_not_found_exception(Exception):
    """Ошибка обращения к отсутствующей сущности."""
    pass


class entity_service(abstract_event_source):
    """Координирует операции сущностей через общий Mapper и репозиторий."""

    # Причины отклонения от наиболее частной к общей.
    __rejections = (
        (entity_not_found_exception, "entity_not_found"),
        (entity_conflict_exception, "entity_conflict"),
        (arguments_exception, "invalid_arguments"),
    )

    def __init__(
        self, repository: abstract_entity_repository, mapper: dto_mapper,
        resources: resource_catalog, create_prototype: Callable[..., prototype],
        *, publish_event: Callable[[operation_event_dto], None] | None = None,
    ) -> None:
        """Получает зависимости для операций с сущностями."""
        self.__repository = repository
        self.__mapper = mapper
        self.__resources = resources
        self.__create_prototype = create_prototype
        self.__publish_event = publish_event

    def set_event_publisher(self, publish_event: Callable[[operation_event_dto], None]) -> None:
        """Подключает публикацию событий CRUD."""
        self.__publish_event = publish_event

    def model_type(self, resource: str) -> type:
        """Возвращает тип модели зарегистрированного ресурса."""
        return self.__resources.model_type(resource)

    def get(self, resource: str, code: str) -> abstract_dto:
        """Читает сущность по коду и возвращает её DTO."""
        with self.__track(crud_operation.GET, resource, code):
            return self.__read_dto(self.model_type(resource), code)

    def __read_dto(self, model_type: type[entity_model], code: str) -> abstract_dto:
        """Читает DTO, в том числе для подготовки изменения."""
        model = self.__repository.find(model_type, code)
        if model is None:
            raise entity_not_found_exception("Сущность не найдена")
        return self.__mapper.to_dto(model)

    def list(self, resource: str) -> tuple[entity_summary_dto, ...]:
        """Возвращает краткие DTO сущностей выбранного ресурса."""
        with self.__track(crud_operation.LIST, resource):
            return self.__summaries(self.__repository.list(self.model_type(resource)))

    def search(
        self, resource: str, criteria: filter_dto | Callable[[], filter_dto],
    ) -> tuple[entity_summary_dto, ...]:
        """Отбирает и сортирует доменные модели до преобразования в краткие DTO."""
        with self.__track(crud_operation.SEARCH, resource):
            if not isinstance(criteria, filter_dto) and callable(criteria):
                criteria = criteria()
            model = self.__resources.search_model_type(resource)
            source = self.__create_prototype(self.__repository.list(model), criteria, model)
            return self.__summaries(source.clone().data)

    @staticmethod
    def __summaries(models: Iterable[entity_model]) -> tuple[entity_summary_dto, ...]:
        """Преобразует сущности списка или поиска в одинаковое представление."""
        return tuple(entity_summary_dto(code=model.unique_code, name=model.name) for model in models)

    def create(
        self, dto: abstract_dto | Callable[[], abstract_dto], *, resource: str | None = None,
    ) -> abstract_dto:
        """Создаёт модель через Mapper, регистрирует её и возвращает DTO."""
        with self.__track(crud_operation.CREATE, resource) as entity:
            if not isinstance(dto, abstract_dto) and callable(dto):
                dto = dto()
            model = self.__mapper.to_model(dto)
            self.__repository.add(type(model), model)
            entity["entity_code"] = model.unique_code
            return self.__mapper.to_dto(model)

    def change(
        self, resource: str, code: str, dto: abstract_dto | Callable[[type[abstract_dto]], abstract_dto],
    ) -> abstract_dto:
        """Атомарно применяет частичный DTO, сохраняя идентичность сущности."""
        with self.__track(crud_operation.CHANGE, resource, code) as entity:
            model_type = self.model_type(resource)
            if not isinstance(dto, abstract_dto) and callable(dto):
                dto = dto(type(self.__read_dto(model_type, code)))
            model = self.__repository.change(model_type, code, lambda current: self.__mapper.to_model(dto, current))
            if model is None:
                raise entity_not_found_exception("Сущность не найдена")
            entity["entity_code"] = model.unique_code
            return self.__mapper.to_dto(model)

    def delete(self, resource: str, code: str) -> None:
        """Удаляет сущность через репозиторий с проверкой входящих ссылок."""
        with self.__track(crud_operation.DELETE, resource, code):
            if not self.__repository.delete(self.model_type(resource), code):
                raise entity_not_found_exception("Сущность не найдена")

    @contextmanager
    def __track(
        self, operation: crud_operation, resource: str | None, code: str | None = None,
    ) -> Generator[dict[str, str | None], None, None]:
        """Публикует начало и один итог, сохраняя исходное исключение операции."""
        entity = {
            "entity_type": (resource.strip().lower() or None) if isinstance(resource, str) else None,
            "entity_code": (code.strip() or None) if isinstance(code, str) else None,
        }
        publish_event = self.__publish_event
        if publish_event is None:
            yield entity
            return

        def publish(phase: event_phase, reason_code: str | None = None) -> None:
            """Передаёт диспетчеру текущее состояние операции."""
            publish_event(operation_event_dto(
                subsystem=log_subsystem.CRUD, operation=operation, phase=phase, reason_code=reason_code, **entity,
            ))

        publish(event_phase.STARTED)
        try:
            yield entity
        except Exception as error:
            reason_code = next((reason for error_type, reason in self.__rejections if isinstance(error, error_type)), None)
            if reason_code is None:
                publish(event_phase.FAILED, type(error).__name__)
            else:
                publish(event_phase.REJECTED, reason_code)
            raise
        else:
            publish(event_phase.COMPLETED)
