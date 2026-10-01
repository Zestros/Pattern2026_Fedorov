from Src.Core.abstract_model import abstract_model
from Src.Models.company_model import company_model
from Src.Core.validator import validator

class settings_model(abstract_model):
    # Карточка организации
    __company: company_model = None
    # Наименование директора
    __boss_name: str = ""
    # Наименование главного бухгалтера
    __account_name: str = ""
    # Флаг первого старта
    __first_start: bool = True

    @property
    def company(self) -> company_model:
        return self.__company

    @company.setter
    def company(self, value: company_model) -> None:
        validator.validate(value, company_model)
        self.__company = value

    @property
    def boss_name(self) -> str:
        return self.__boss_name

    @boss_name.setter
    def boss_name(self, value: str) -> None:
        validator.validate(value, str, 255)
        self.__boss_name = value.strip()

    @property
    def account_name(self) -> str:
        return self.__account_name

    @account_name.setter
    def account_name(self, value: str) -> None:
        validator.validate(value, str, 255)
        self.__account_name = value.strip()

    @property
    def first_start(self) -> bool:
        return self.__first_start

    @first_start.setter
    def first_start(self, value: bool) -> None:
        validator.validate(value, bool, field="first_start")
        self.__first_start = value