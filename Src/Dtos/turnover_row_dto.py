from Src.Core.abstract_dto import abstract_dto
from Src.Core.exception import arguments_exception
from Src.Core.validator import validator


class turnover_row_dto(abstract_dto):
    """Строка складской ОСВ по складу и номенклатуре."""

    @property
    def warehouse_code(self) -> str:
        """Возвращает код склада."""
        return self.__warehouse_code

    @warehouse_code.setter
    def warehouse_code(self, value: str) -> None:
        """Проверяет и сохраняет непустой код склада."""
        validator.validate(value, str, field="warehouse_code")
        object.__setattr__(self, "_turnover_row_dto__warehouse_code", value)

    @property
    def warehouse_name(self) -> str:
        """Возвращает наименование склада."""
        return self.__warehouse_name

    @warehouse_name.setter
    def warehouse_name(self, value: str) -> None:
        """Проверяет и сохраняет непустое наименование склада."""
        validator.validate(value, str, field="warehouse_name")
        object.__setattr__(self, "_turnover_row_dto__warehouse_name", value)

    @property
    def item_code(self) -> str:
        """Возвращает код номенклатуры."""
        return self.__item_code

    @item_code.setter
    def item_code(self, value: str) -> None:
        """Проверяет и сохраняет непустой код номенклатуры."""
        validator.validate(value, str, field="item_code")
        object.__setattr__(self, "_turnover_row_dto__item_code", value)

    @property
    def item_name(self) -> str:
        """Возвращает наименование номенклатуры."""
        return self.__item_name

    @item_name.setter
    def item_name(self, value: str) -> None:
        """Проверяет и сохраняет непустое наименование номенклатуры."""
        validator.validate(value, str, field="item_name")
        object.__setattr__(self, "_turnover_row_dto__item_name", value)

    @property
    def unit_code(self) -> str:
        """Возвращает код базовой единицы."""
        return self.__unit_code

    @unit_code.setter
    def unit_code(self, value: str) -> None:
        """Проверяет и сохраняет непустой код базовой единицы."""
        validator.validate(value, str, field="unit_code")
        object.__setattr__(self, "_turnover_row_dto__unit_code", value)

    @property
    def unit_name(self) -> str:
        """Возвращает наименование базовой единицы."""
        return self.__unit_name

    @unit_name.setter
    def unit_name(self, value: str) -> None:
        """Проверяет и сохраняет непустое наименование базовой единицы."""
        validator.validate(value, str, field="unit_name")
        object.__setattr__(self, "_turnover_row_dto__unit_name", value)

    @property
    def opening(self) -> int | float:
        """Возвращает начальный остаток."""
        return self.__opening

    @opening.setter
    def opening(self, value: int | float) -> None:
        """Проверяет и сохраняет начальный остаток с учётом знака."""
        self.__validate_balance(value, "opening")
        object.__setattr__(self, "_turnover_row_dto__opening", value)

    @property
    def receipts(self) -> int | float:
        """Возвращает количество поступлений."""
        return self.__receipts

    @receipts.setter
    def receipts(self, value: int | float) -> None:
        """Проверяет и сохраняет неотрицательное количество поступлений."""
        validator.validate_number(value, "receipts")
        object.__setattr__(self, "_turnover_row_dto__receipts", value)

    @property
    def issues(self) -> int | float:
        """Возвращает количество списаний."""
        return self.__issues

    @issues.setter
    def issues(self, value: int | float) -> None:
        """Проверяет и сохраняет неотрицательное количество списаний."""
        validator.validate_number(value, "issues")
        object.__setattr__(self, "_turnover_row_dto__issues", value)

    @property
    def closing(self) -> int | float:
        """Возвращает конечный остаток."""
        return self.__closing

    @closing.setter
    def closing(self, value: int | float) -> None:
        """Проверяет и сохраняет конечный остаток с учётом знака."""
        self.__validate_balance(value, "closing")
        object.__setattr__(self, "_turnover_row_dto__closing", value)

    @staticmethod
    def __validate_balance(value: int | float, field: str) -> None:
        """Проверяет конечное число, разрешая отрицательный остаток."""
        if type(value) not in (int, float):
            raise arguments_exception(field, "Ожидается число")
        validator.validate_number(abs(value), field)
