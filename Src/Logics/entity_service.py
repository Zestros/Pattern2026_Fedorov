from Src.Core.abstract_dto import abstract_dto
from Src.Core.abstract_entity_repository import abstract_entity_repository
from Src.Dtos.entity_dto import entity_summary_dto
from Src.Logics.dto_mapping import dto_mapper
from Src.Logics.resource_catalog import resource_catalog


class entity_not_found_exception(Exception):
    """Ошибка обращения к отсутствующей сущности."""
    pass


class entity_service:
    """Координирует операции сущностей через общий Mapper и репозиторий."""
    def __init__(self, repository: abstract_entity_repository, mapper: dto_mapper, resources: resource_catalog) -> None:
        """Получает зависимости для операций с сущностями."""
        self.__repository = repository
        self.__mapper = mapper
        self.__resources = resources

    def model_type(self, resource: str) -> type:
        """Возвращает тип модели зарегистрированного ресурса."""
        return self.__resources.model_type(resource)

    def get(self, resource: str, code: str) -> abstract_dto:
        """Читает сущность по коду и возвращает её DTO."""
        model = self.__repository.find(self.model_type(resource), code)
        if model is None:
            raise entity_not_found_exception("Сущность не найдена")
        return self.__mapper.to_dto(model)

    def list(self, resource: str) -> tuple[entity_summary_dto, ...]:
        """Возвращает краткие DTO сущностей выбранного ресурса."""
        return tuple(entity_summary_dto(code=model.unique_code, name=model.name)
                     for model in self.__repository.list(self.model_type(resource)))

    def create(self, dto: abstract_dto) -> abstract_dto:
        """Создаёт модель через Mapper, регистрирует её и возвращает DTO."""
        model = self.__mapper.to_model(dto)
        self.__repository.add(type(model), model)
        return self.__mapper.to_dto(model)

    def change(self, resource: str, code: str, dto: abstract_dto) -> abstract_dto:
        """Атомарно применяет частичный DTO, сохраняя идентичность сущности."""
        model = self.__repository.change(self.model_type(resource), code,
                                        lambda current: self.__mapper.to_model(dto, current))
        if model is None:
            raise entity_not_found_exception("Сущность не найдена")
        return self.__mapper.to_dto(model)

    def delete(self, resource: str, code: str) -> None:
        """Удаляет сущность через репозиторий с проверкой входящих ссылок."""
        if not self.__repository.delete(self.model_type(resource), code):
            raise entity_not_found_exception("Сущность не найдена")
