from Src.Core.abstract_manager import abstract_manager
import json
from Src.Core.validator import validator, operation_exception
from Src.Models.settings_model import settings_model
from Src.Models.company_model import company_model

class setting_manager(abstract_manager):
    __default_file_name: str = 'settings.json'
    __settings: settings_model = None

    def __new__(cls):
        """Создаёт единственный экземпляр или возвращает существующий."""
        if not hasattr(cls, 'instance'):
            cls.instance = super(setting_manager, cls).__new__(cls)
        return cls.instance

    def load(self, file_name = ""):
        inner_file_name = file_name if file_name.strip() != "" else self.__default_file_name
        validator.validate(inner_file_name, str)

        try:
            with open(inner_file_name, "r") as file:
                self._data = json.load(file)
        except Exception as ec:
            raise operation_exception(
                "Не удалось загрузить файл настроек"
            )

        self._is_loaded = self.convert()

    @property
    def settings(self) -> settings_model:
        return self.__settings

    def convert(self) -> bool:
        """Преобразует исходные данные в модель настроек."""
        try:
            data = self._data

            required_fields = (
                "company",
                "boss_name",
                "account_name",
                "first_start",
            )

            for field in required_fields:
                if field not in data:
                    raise operation_exception(
                        f"Отсутствует обязательное поле: {field}"
                    )

            settings = settings_model()
            settings.company = company_model(**data["company"])
            settings.boss_name = data["boss_name"]
            settings.account_name = data["account_name"]
            settings.first_start = data["first_start"]

            self.__settings = settings
            return True
        except operation_exception:
            raise
        except Exception as error:
            raise operation_exception(
                "Не удалось преобразовать настройки"
            )
