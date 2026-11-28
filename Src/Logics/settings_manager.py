from collections.abc import Callable
from threading import RLock

from Src.Core.abstract_event_source import abstract_event_source
from Src.Core.abstract_manager import abstract_manager
from Src.Core.event_phase import event_phase
from Src.Core.exception import arguments_exception
from Src.Core.log_subsystem import log_subsystem
from Src.Core.validator import validator, operation_exception
from Src.Dtos.operation_event_dto import operation_event_dto
from Src.Logics.reference_restore import reference_restore
from Src.Models.settings_model import settings_model


class setting_manager(abstract_manager, abstract_event_source):
    """Загружает и хранит настройки приложения."""

    __default_file_name: str = 'settings.json'
    __settings: settings_model = None
    __load_lock = RLock()
    __publish_event: Callable[[operation_event_dto], None] | None = None

    def __new__(cls, *, publish_event: Callable[[operation_event_dto], None] | None = None):
        """Создаёт единственный экземпляр или возвращает существующий."""
        if not hasattr(cls, 'instance'):
            cls.instance = super(setting_manager, cls).__new__(cls)
        return cls.instance

    def __init__(self, *, publish_event: Callable[[operation_event_dto], None] | None = None) -> None:
        """Подключает переданного издателя перед первой загрузкой настроек."""
        if publish_event is not None:
            self.set_event_publisher(publish_event)

    def set_event_publisher(self, publish_event: Callable[[operation_event_dto], None]) -> None:
        """Подключает публикацию результатов загрузки настроек."""
        with self.__load_lock:
            self.__publish_event = publish_event

    def load(self, file_name: str = "") -> None:
        """Читает JSON и сообщает об успешной загрузке или изменении настроек."""
        if not isinstance(file_name, str):
            raise arguments_exception("file_name", "Ожидается имя файла")
        inner_file_name = file_name if file_name.strip() else self.__default_file_name

        with self.__load_lock:
            previous = self.__settings
            try:
                self._data = reference_restore.read_json(inner_file_name)
            except (OSError, ValueError) as error:
                raise operation_exception("Не удалось загрузить файл настроек") from error
            self._is_loaded = self.convert()
            current = self.__settings
            publish_event = self.__publish_event

        if publish_event is None:
            return
        if previous is None:
            publish_event(operation_event_dto(
                subsystem=log_subsystem.SETTINGS, operation="load", phase=event_phase.COMPLETED,
            ))
            return

        before = self.__parameter_values(previous)
        after = self.__parameter_values(current)
        changed_fields = tuple(name for name, value in after.items() if value != before[name])
        if changed_fields:
            publish_event(operation_event_dto(
                subsystem=log_subsystem.SETTINGS, operation="change", phase=event_phase.COMPLETED,
                details={"changed_fields": changed_fields},
            ))

    @staticmethod
    def __parameter_values(settings: settings_model) -> dict[str, object]:
        """Собирает параметры и сравнивает организацию по её реквизитам."""
        values = {
            name: getattr(settings, name) for name in settings.field_names() if name != "unique_code"
        }
        if settings.company is not None:
            company = settings.company
            values["company"] = tuple(getattr(company, name) for name in company.constructor_fields())
        return values

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
