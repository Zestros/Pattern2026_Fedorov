from Src.Core.abstract_manager import abstract_manager
from Src.Core.exception import arguments_exception
from Src.Core.validator import validator, operation_exception
from Src.Logics.reference_restore import reference_restore
from Src.Models.settings_model import settings_model

class setting_manager(abstract_manager):
    __default_file_name: str = 'settings.json'
    __settings: settings_model = None

    def __new__(cls):
        """Создаёт единственный экземпляр или возвращает существующий."""
        if not hasattr(cls, 'instance'):
            cls.instance = super(setting_manager, cls).__new__(cls)
        return cls.instance

    def load(self, file_name: str = "") -> None:
        """Читает JSON и публикует настройки после успешного восстановления."""
        if not isinstance(file_name, str):
            raise arguments_exception("file_name", "Ожидается имя файла")
        inner_file_name = file_name if file_name.strip() else self.__default_file_name
        try:
            self._data = reference_restore.read_json(inner_file_name)
        except (OSError, ValueError) as error:
            raise operation_exception("Не удалось загрузить файл настроек") from error

        self._is_loaded = self.convert()

    @property
    def settings(self) -> settings_model:
        """Возвращает последнюю успешно загруженную модель настроек."""
        return self.__settings

    def convert(self) -> bool:
        """Преобразует исходные данные в модель настроек."""
        try:
            data = self._data
            validator.validate(data, dict, field="settings")
            # Поля, которые требует файл настроек приложения.
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
                if data[field] is None:
                    raise arguments_exception(field, "Ожидается значение поля")

            self.__settings = reference_restore().restore_model(data, settings_model)
            return True
        except arguments_exception as error:
            raise operation_exception(f"Не удалось преобразовать настройки. {error}") from error
