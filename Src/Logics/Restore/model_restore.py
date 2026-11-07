from inspect import Parameter, getattr_static, signature

from Src.Core.abstract_model import abstract_model
from Src.Core.abstract_restore_handler import abstract_restore_handler
from Src.Core.exception import arguments_exception


class model_restore(abstract_restore_handler):
    """Восстанавливает модель через конструктор и публичные изменяемые поля."""

    def __init__(self, model_type: type) -> None:
        """Читает именованные параметры из сигнатуры конструктора модели."""
        self.model_type = model_type
        self.type_name = model_type.__name__
        parameters = list(signature(model_type.__init__).parameters.values())[1:]
        self.constructor_fields = [
            parameter.name for parameter in parameters
            if parameter.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
        ]
        self.handled_fields = set(self.constructor_fields)
        self.expected_fields = {"$id", "$type", "$fields"}

    def validate(self, node: dict) -> None:
        """Проверяет, что состояние модели содержит публичные именованные поля."""
        super().validate(node)
        fields = node["$fields"]
        if not isinstance(fields, dict) or any(
            not isinstance(name, str) or name.startswith("_") for name in fields
        ):
            raise arguments_exception("$fields", "Ожидаются публичные именованные поля")

    def children(self, node: dict) -> list:
        """Возвращает значения свойств для предварительного обхода графа."""
        return list(node["$fields"].values())

    def allocate(self, node: dict) -> object:
        """Создаёт экземпляр без инициализации для регистрации обратных ссылок."""
        return self.model_type.__new__(self.model_type)

    def restore(self, instance: object, node: dict, reader) -> object:
        """Восстанавливает аргументы, выполняет конструктор и заполняет остальные поля."""
        fields = {name: reader.restore_value(value) for name, value in node["$fields"].items()}
        self.initialize(instance, fields)
        self.fill_fields(instance, fields)
        return instance

    def initialize(self, instance: object, fields: dict) -> None:
        """Передаёт найденные в JSON аргументы конструктору модели."""
        arguments = {name: fields[name] for name in self.constructor_fields if name in fields}
        self.model_type.__init__(instance, **arguments)

    def fill_fields(self, instance: object, fields: dict) -> None:
        """Сохраняет доменный код и дополнительные публичные поля без обхода свойств."""
        handled = self.handled_fields.copy()
        if isinstance(instance, abstract_model):
            instance.unique_code = fields["unique_code"]
            handled.add("unique_code")
        for name, value in fields.items():
            if name in handled:
                continue
            descriptor = getattr_static(type(instance), name, None)
            if isinstance(descriptor, property) and descriptor.fset is None:
                raise arguments_exception(name, "Неизвестное поле только для чтения")
            setattr(instance, name, value)
