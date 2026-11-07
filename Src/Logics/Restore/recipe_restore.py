from Src.Core.exception import arguments_exception
from Src.Logics.Restore.model_restore import model_restore
from Src.Models.recipe_model import recipe_model


class recipe_restore(model_restore):
    """Восстанавливает карту до её строк и проверяет пересчитанные массы."""

    def __init__(self) -> None:
        """Отделяет аргументы карты, её строки и вычисляемые свойства."""
        super().__init__(recipe_model)
        self.computed_fields = {"gross_weight", "net_weight", "packaging_weight"}
        self.handled_fields.update(self.computed_fields | {"ingredients"})

    def restore(self, instance: recipe_model, node: dict, reader) -> recipe_model:
        """Создаёт пустую карту, затем добавляет строки через публичный метод."""
        source = node["$fields"]
        header = {
            name: reader.restore_value(source[name])
            for name in self.constructor_fields if name in source
        }
        self.initialize(instance, header)
        instance.unique_code = source["unique_code"]
        fields = {name: reader.restore_value(value) for name, value in source.items()}
        for ingredient in fields["ingredients"]:
            instance.add_ingredient(ingredient)
        self.fill_fields(instance, fields)
        return instance

    def check(self, instance: recipe_model, node: dict) -> None:
        """Сверяет расчётные свойства только после заполнения всего графа."""
        fields = node["$fields"]
        for name in self.computed_fields & fields.keys():
            if getattr(instance, name) != fields[name]:
                raise arguments_exception(name, "Расчётное поле не соответствует восстановленной модели")
