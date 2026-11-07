from Src.Logics.Restore.model_restore import model_restore
from Src.Models.settings_model import settings_model


class settings_restore(model_restore):
    """Восстанавливает настройки с учётом необязательных начальных значений."""

    def __init__(self) -> None:
        """Регистрирует поля настроек, заполняемые через их свойства."""
        super().__init__(settings_model)
        self.handled_fields.update({"company", "boss_name", "account_name", "first_start", "response_format"})

    def initialize(self, instance: settings_model, fields: dict) -> None:
        """Применяет заданные значения, сохраняя допустимые пустые значения по умолчанию."""
        super().initialize(instance, fields)
        for name in ("company", "boss_name", "account_name"):
            if fields[name] not in (None, ""):
                setattr(instance, name, fields[name])
        instance.first_start = fields["first_start"]
        instance.response_format = fields["response_format"]
