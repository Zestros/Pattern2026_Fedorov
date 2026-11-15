from Src.Core.abstract_model import abstract_model
from Src.Core.exception import arguments_exception
from Src.Logics.Restore.abstract_object_restore import abstract_object_restore


class model_restore(abstract_object_restore):
    """Собирает модель из полей конструктора и связанных объектов."""

    def __init__(self, model_type: type[abstract_model]) -> None:
        """Запоминает зарегистрированный класс и его полное имя."""
        self.model_type = model_type
        self.type_name = model_type.type_name()

    def validate(self, node: dict) -> None:
        """Проверяет допустимые и обязательные поля модели."""
        super().validate(node)
        self.model_type.validate_restore_fields(node["$fields"])

    def allocate(self, node: dict) -> abstract_model:
        """Выделяет модель заранее для регистрации ссылок."""
        return self.model_type.__new__(self.model_type)

    def restore(self, instance: abstract_model, node: dict, reader) -> abstract_model:
        """Инициализирует модель до обхода полей, заполняемых после конструктора."""
        source = node["$fields"]
        initial = {
            name: reader.restore_value(source[name])
            for name in self.model_type.initial_restore_fields() if name in source
        }
        self.restore_fields(instance, initial)
        remaining = {
            name: reader.restore_value(value)
            for name, value in source.items()
            if name not in initial and name not in self.model_type.computed_fields
        }
        if remaining:
            instance.apply_fields(remaining)
        return instance

    def restore_fields(
        self, instance: abstract_model, fields: dict[str, object],
    ) -> abstract_model:
        """Восстанавливает именно тот экземпляр, который хранится в таблице ссылок."""
        result = self.model_type.from_fields(fields, instance=instance)
        if result is not instance:
            raise arguments_exception("instance", "Фабричный метод должен заполнить выделенный экземпляр")
        return result

    def check(self, instance: abstract_model, node: dict) -> None:
        """Поручает модели сверку расчётных значений после связывания графа."""
        instance.check_computed_fields(node["$fields"])
