from Src.Core.abstract_report import abstract_report
from Src.Models.recipe_model import recipe_model
from Src.Core.validator import validator
from Src.Core.report_result_dto import report_result_dto


class text_report(abstract_report):
    __recipe: recipe_model

    def build(self, source):
        validator.validate(source, recipe_model)
        self.__recipe = source

        header = "Код | Наименование | Брутто | Нетто"
        data = []

        for item in self.__recipe.ingredients:
            data.append(
                f"{item.unique_code} | {item.item.name} | "
                f"{item.calculate_gross_weight(source.mass_unit)} | "
                f"{item.calculate_net_weight(source.mass_unit)}"
            )

        result = report_result_dto()
        result.text = "\n".join([header, *data])

        return result
