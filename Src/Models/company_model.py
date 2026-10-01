from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception


class company_model(entity_model):
    """Организация с наименованием и обязательными реквизитами."""

    # Идентификационный номер налогоплательщика.
    __inn: str

    # Банковский идентификационный код.
    __bik: str

    # Номер банковского счёта.
    __account: str

    # Форма собственности в обозначении, принятом в задании.
    __ownership_form: str

    def __init__(
        self,
        name: str,
        inn: str,
        bik: str,
        account: str,
        ownership_form: str,
    ) -> None:
        """Создаёт организацию и проверяет переданные реквизиты."""
        super().__init__()
        self.name = name
        self.inn = inn
        self.bik = bik
        self.account = account
        self.ownership_form = ownership_form

    @staticmethod
    def _validate_requisite(value: str, field: str) -> str:
        """Проверяет строковый реквизит и удаляет пробелы по краям."""
        if not isinstance(value, str):
            raise arguments_exception(
                field,
                "Реквизит должен быть строкой",
            )

        requisite = value.strip()

        if requisite == "":
            raise arguments_exception(
                field,
                "Реквизит не может быть пустым",
            )

        return requisite

    @property
    def inn(self) -> str:
        """Возвращает ИНН организации."""
        return self.__inn

    @inn.setter
    def inn(self, value: str) -> None:
        """Устанавливает непустой строковый ИНН."""
        self.__inn = self._validate_requisite(value, "inn")

    @property
    def bik(self) -> str:
        """Возвращает БИК банка организации."""
        return self.__bik

    @bik.setter
    def bik(self, value: str) -> None:
        """Устанавливает непустой строковый БИК."""
        self.__bik = self._validate_requisite(value, "bik")

    @property
    def account(self) -> str:
        """Возвращает номер банковского счёта организации."""
        return self.__account

    @account.setter
    def account(self, value: str) -> None:
        """Устанавливает непустой строковый номер счёта."""
        self.__account = self._validate_requisite(value, "account")

    @property
    def ownership_form(self) -> str:
        """Возвращает форму собственности организации."""
        return self.__ownership_form

    @ownership_form.setter
    def ownership_form(self, value: str) -> None:
        """Устанавливает непустое строковое обозначение формы собственности."""
        self.__ownership_form = self._validate_requisite(
            value,
            "ownership_form",
        )