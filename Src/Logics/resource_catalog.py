from Src.Core.abstract_dto import abstract_dto
from Src.Core.exception import arguments_exception
from Src.Logics.dto_mapping import mapping_registry


class resource_definition:
    """Внешнее имя, основной DTO и признаки специализированных контрактов."""
    def __init__(self, name: str, dto_type: type[abstract_dto], variants: dict | None = None,
                 *, searchable: bool = True) -> None:
        """Сохраняет варианты входного контракта и доступность поиска."""
        self.name = name
        self.dto_type = dto_type
        self.variants = variants or {}
        self.searchable = searchable


class resource_catalog:
    """Разрешает имена ресурсов без чтения данных или внутренних полей Mapper."""
    def __init__(self, mappings: mapping_registry, definitions: tuple[resource_definition, ...]) -> None:
        """Проверяет уникальность имён и наличие маппингов всех вариантов."""
        self.__mappings = mappings
        self.__definitions = {item.name: item for item in definitions}
        if len(self.__definitions) != len(definitions):
            raise ValueError("Повторная регистрация ресурса")
        for item in definitions:
            base = mappings.for_type(item.dto_type).model
            for variant in item.variants.values():
                if not issubclass(mappings.for_type(variant).model, base):
                    raise ValueError("Вариант ресурса должен наследовать его модель")

    def resource(self, name: str) -> resource_definition:
        """Возвращает определение ресурса или ошибку неизвестного имени."""
        if not isinstance(name, str):
            raise arguments_exception("entity_type", "Ожидается имя ресурса")
        try:
            return self.__definitions[name.strip().lower()]
        except KeyError as error:
            raise arguments_exception("entity_type", "Неизвестный ресурс") from error

    def model_type(self, name: str) -> type:
        """Возвращает зарегистрированный доменный тип ресурса."""
        return self.__mappings.for_type(self.resource(name).dto_type).model

    def search_model_type(self, name: str) -> type:
        """Возвращает доменный тип ресурса, у которого доступен поиск."""
        resource = self.resource(name)
        if not resource.searchable:
            raise arguments_exception("entity_type", "Поиск по этому ресурсу недоступен")
        return self.__mappings.for_type(resource.dto_type).model

    def request_type(self, name: str, fields: dict) -> type[abstract_dto]:
        """Выбирает DTO по присутствующему признаку, отклоняя неоднозначность."""
        resource = self.resource(name)
        variants = [dto for field, dto in resource.variants.items() if field in fields]
        if len(variants) > 1:
            raise arguments_exception("body", "Неоднозначный тип ресурса")
        return variants[0] if variants else resource.dto_type
