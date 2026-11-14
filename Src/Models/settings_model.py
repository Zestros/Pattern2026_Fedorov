from Src.Core.report_type_enum import report_type_enum
from Src.Core.abstract_model import abstract_model
from Src.Models.company_model import company_model
from Src.Core.validator import validator


class settings_model(abstract_model):
    """Хранит настройки организации, первого запуска и формата отчётов."""

    # Карточка организации
    __company: company_model | None = None
    # Наименование директора
    __boss_name: str = ""
    # Наименование главного бухгалтера
    __account_name: str = ""
    # Флаг первого старта
    __first_start: bool = True

    @property
    def company(self) -> company_model | None:
        """Возвращает организацию, если она указана."""
        return self.__company

    @company.setter
    def company(self, value: company_model | None) -> None:
        """Устанавливает организацию или очищает её."""
        if value is not None:
            validator.validate(value, company_model, field="company")
        self.__company = value

    @property
    def boss_name(self) -> str:
        """Возвращает имя директора или пустую строку."""
        return self.__boss_name

    @boss_name.setter
    def boss_name(self, value: str) -> None:
        """Устанавливает имя директора; пустая строка очищает имя."""
        if not isinstance(value, str) or value != "":
            validator.validate(value, str, 255, field="boss_name")
        self.__boss_name = value.strip()

    @property
    def account_name(self) -> str:
        """Возвращает имя главного бухгалтера или пустую строку."""
        return self.__account_name

    @account_name.setter
    def account_name(self, value: str) -> None:
        """Устанавливает имя главного бухгалтера; пустая строка очищает имя."""
        if not isinstance(value, str) or value != "":
            validator.validate(value, str, 255, field="account_name")
        self.__account_name = value.strip()

    @property
    def first_start(self) -> bool:
        """Возвращает признак заполнения стартовыми данными."""
        return self.__first_start

    @first_start.setter
    def first_start(self, value: bool) -> None:
        """Устанавливает признак первого запуска."""
        validator.validate(value, bool, field="first_start")
        self.__first_start = value

    __response_format: report_type_enum = report_type_enum.TXT

    @property
    def response_format(self) -> report_type_enum:
        """Возвращает формат отчёта по умолчанию."""
        return self.__response_format

    @response_format.setter
    def response_format(self, value: report_type_enum) -> None:
        """Устанавливает поддерживаемый формат отчёта."""
        validator.validate(value, report_type_enum, field="response_format")
        self.__response_format = value
