from Src.Core.abstract_model import abstract_model
from Src.Core.exception import arguments_exception
from Src.Logics.Restore.abstract_object_restore import abstract_object_restore


class model_restore(abstract_object_restore):
    """Поручает создание модели её фабричному методу."""

    def __init__(self, model_type: type[abstract_model]) -> None:
        """Запоминает зарегистрированный класс и его полное имя."""
        self.model_type = model_type
        self.type_name = model_type.type_name()

    def validate(self, node: dict) -> None:
        """Проверяет наличие сохранённого доменного кода."""
        super().validate(node)
        self.model_type.validate_fields(node["$fields"])
        if "unique_code" not in node["$fields"]:
            raise arguments_exception("unique_code", "В модели должен быть указан доменный код")

    def allocate(self, node: dict) -> abstract_model:
        """Выделяет модель заранее для регистрации ссылок."""
        return self.model_type.__new__(self.model_type)

    def restore_fields(
        self, instance: abstract_model, fields: dict[str, object],
    ) -> abstract_model:
        """Восстанавливает именно тот экземпляр, который хранится в таблице ссылок."""
        result = self.model_type.from_fields(fields, instance=instance)
        if result is not instance:
            raise arguments_exception("instance", "Фабричный метод должен заполнить выделенный экземпляр")
        return result
