from Src.Core.exception import arguments_exception
from Src.Logics.Restore.model_restore import model_restore
from Src.Models.unit_model import unit_model


class unit_restore(model_restore):
    """Восстанавливает единицу и её самоссылку средствами конструктора модели."""

    def __init__(self) -> None:
        """Регистрирует аргументы конструктора единицы."""
        super().__init__(unit_model)

    def initialize(self, instance: unit_model, fields: dict) -> None:
        """Распознаёт ссылку на создаваемый экземпляр перед вызовом конструктора."""
        base = fields["base_unit"]
        if base is None:
            raise arguments_exception("base_unit", "В графе база должна быть объектом или ссылкой")
        arguments = dict(fields)
        arguments["base_unit"] = None if base is instance else base
        super().initialize(instance, arguments)
