from Src.Core.exception import arguments_exception
from Src.Logics.Restore.model_restore import model_restore
from Src.Models.recipe_model import recipe_model


class recipe_restore(model_restore):
    """Читает заголовок карты до строк и проверяет пересчитанные массы."""

    # Расчётные свойства проверяются после восстановления связей.
    computed_fields = {"gross_weight", "net_weight", "packaging_weight"}

    def __init__(self) -> None:
        """Регистрирует рецепт и определяет поля его заголовка."""
        super().__init__(recipe_model)
        self.header_fields = (*recipe_model.constructor_fields(), "unique_code")

    def validate(self, node: dict) -> None:
        """Проверяет наличие коллекции строк карты."""
        super().validate(node)
        if "ingredients" not in node["$fields"]:
            raise arguments_exception("ingredients", "В рецепте должны быть указаны строки")

    def restore(self, instance: recipe_model, node: dict, reader) -> recipe_model:
        """Инициализирует заголовок до восстановления вложенных объектов."""
        source = node["$fields"]
        header = {
            name: reader.restore_value(source[name])
            for name in self.header_fields if name in source
        }
        self.restore_fields(instance, header)
        details = {
            name: reader.restore_value(value)
            for name, value in source.items()
            if name not in header and name not in self.computed_fields
        }
        instance.apply_fields(details)
        return instance

    def check(self, instance: recipe_model, node: dict) -> None:
        """Сверяет расчётные свойства после заполнения всего графа."""
        fields = node["$fields"]
        for name in self.computed_fields & fields.keys():
            if getattr(instance, name) != fields[name]:
                raise arguments_exception(name, "Расчётное поле не соответствует восстановленной модели")
