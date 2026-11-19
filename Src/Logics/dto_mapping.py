from inspect import signature
from collections.abc import Callable
from Src.Core.abstract_dto import abstract_dto
from Src.Core.abstract_entity_repository import abstract_entity_repository
from Src.Core.abstract_model import abstract_model
from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception


class model_mapping:
    """Регистрация типа и особых операций заполнения агрегата."""
    def __init__(self, dto: type[abstract_dto], model: type[abstract_model],
                 writers: dict[str, Callable] | None = None,
                 factory: Callable | None = None) -> None:
        """Регистрирует типы, параметры конструктора и особые способы заполнения."""
        self.dto = dto
        self.model = model
        self.factory = factory
        self.parameters = frozenset(signature(model).parameters)
        self.writers = writers or {}


class mapping_registry:
    """Хранит только соответствия DTO и доменных моделей."""
    def __init__(self, mappings: tuple[model_mapping, ...]) -> None:
        """Строит индексы типов и отклоняет повторные регистрации."""
        self.__dto = {mapping.dto: mapping for mapping in mappings}
        self.__model = {mapping.model: mapping for mapping in mappings}
        if len(self.__dto) != len(mappings) or len(self.__model) != len(mappings):
            raise ValueError("Повторная регистрация маппинга")

    def for_type(self, dto_type: type[abstract_dto]) -> model_mapping:
        """Возвращает регистрацию по типу DTO без знания внешних ресурсов."""
        return self.__dto[dto_type]

    def for_dto(self, dto: abstract_dto) -> model_mapping:
        """Находит регистрацию для конкретного типа DTO."""
        return self.__dto[type(dto)]

    def for_model(self, model: abstract_model) -> model_mapping:
        """Находит регистрацию для конкретного типа доменной модели."""
        return self.__model[type(model)]


class dto_mapper:
    """Преобразует DTO и модели, разрешая ссылки через репозиторий."""
    def __init__(self, registry: mapping_registry, repository: abstract_entity_repository, resources) -> None:
        """Получает реестр контрактов и репозиторий для разрешения ссылок."""
        self.__registry = registry
        self.__resources = resources
        self.__repository = repository

    def to_dto(self, model: abstract_model) -> abstract_dto:
        """Создаёт DTO по объявленному контракту, заменяя внешние связи кодами."""
        mapping = self.__registry.for_model(model)
        values = {}
        for field in mapping.dto.fields():
            value = getattr(model, field.name)
            if field.reference is not None:
                value = value.unique_code if value is not None else None
            else:
                value = self.__export(value)
            values[field.name] = value
        return mapping.dto(**values)

    def __export(self, value: object) -> object:
        """Преобразует вложенные модели и коллекции в данные DTO."""
        if isinstance(value, abstract_model):
            return self.to_dto(value)
        if isinstance(value, (tuple, list)):
            return tuple(self.__export(item) for item in value)
        return value

    def to_model(self, dto: abstract_dto, current: abstract_model | None = None) -> abstract_model:
        """Создаёт валидный кандидат; неизменённые вложенные объекты не копируются."""
        mapping = self.__registry.for_dto(dto)
        if current is not None and type(current) is not mapping.model:
            raise arguments_exception("type", "Тип существующей сущности нельзя изменить")
        values = {}
        for field in mapping.dto.fields():
            if field.read_only:
                continue
            if dto.contains(field.name):
                value = dto.field_value(field.name)
                if field.reference is not None and value is not None:
                    target = self.__resources.model_type(field.reference)
                    value = self.__repository.find(target, value)
                    if value is None:
                        raise arguments_exception(field.name, "Связанная сущность не найдена")
                else:
                    value = self.__import(value)
            elif current is not None:
                value = getattr(current, field.name)
            elif hasattr(type(dto), field.name):
                value = getattr(type(dto), field.name)
            else:
                continue
            values[field.name] = value
        arguments = {key: value for key, value in values.items() if key in mapping.parameters}
        model = mapping.model(**arguments) if mapping.factory is None else mapping.factory(arguments, current)
        for name, value in values.items():
            if name not in mapping.parameters:
                writer = mapping.writers.get(name)
                if writer is not None:
                    writer(model, value)
                else:
                    setattr(model, name, value)
        if isinstance(model, entity_model):
            model.validate_state()
        return model

    def __import(self, value: object) -> object:
        """Восстанавливает вложенные модели и коллекции из данных DTO."""
        if isinstance(value, abstract_dto):
            return self.to_model(value)
        if isinstance(value, tuple):
            return tuple(self.__import(item) for item in value)
        return value
