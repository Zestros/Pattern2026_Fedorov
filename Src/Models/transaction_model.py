from datetime import datetime

from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Core.validator import validator
from Src.Models.item_model import item_model
from Src.Models.unit_model import unit_model
from Src.Models.warehouse_model import warehouse_model


class transaction_model(entity_model):
    """Складское движение с количеством в базовой единице номенклатуры."""

    def __init__(
        self, occurred_at: datetime, warehouse: warehouse_model, item: item_model,
        unit: unit_model, quantity: int | float,
    ) -> None:
        """Фиксирует приход или расход и переводит количество в базовую единицу."""
        self.__validate_arguments(occurred_at, warehouse, item, unit, quantity)
        super().__init__()
        self.name = "Складское движение"
        self.__occurred_at = occurred_at
        self.__warehouse = warehouse
        self.__item = item
        self.__unit = item.unit.base_unit
        self.__quantity = self.__normalize_quantity(quantity, unit, self.__unit)

    @staticmethod
    def __validate_arguments(
        occurred_at: datetime, warehouse: warehouse_model, item: item_model,
        unit: unit_model, quantity: int | float,
    ) -> None:
        """Проверяет типы составляющих движения и величину количества."""
        validator.validate(occurred_at, datetime, field="occurred_at")
        validator.validate(warehouse, warehouse_model, field="warehouse")
        validator.validate(item, item_model, field="item")
        validator.validate(unit, unit_model, field="unit")
        if type(quantity) not in (int, float):
            raise arguments_exception("quantity", "Ожидается число")
        validator.validate_number(abs(quantity), "quantity", allow_zero=False)

    @staticmethod
    def __normalize_quantity(quantity: int | float, unit: unit_model, base_unit: unit_model) -> float:
        """Пересчитывает количество и сохраняет знак прихода или расхода."""
        try:
            base_quantity = unit.convert_to(abs(quantity), base_unit)
        except OverflowError as error:
            raise arguments_exception("quantity", "Количество слишком велико") from error
        validator.validate_number(base_quantity, "quantity", allow_zero=False)
        return -base_quantity if quantity < 0 else base_quantity

    @property
    def occurred_at(self) -> datetime:
        """Возвращает дату и время движения."""
        return self.__occurred_at

    @property
    def warehouse(self) -> warehouse_model:
        """Возвращает склад, на котором произошло движение."""
        return self.__warehouse

    @property
    def item(self) -> item_model:
        """Возвращает номенклатуру, по которой зарегистрировано движение."""
        return self.__item

    @property
    def unit(self) -> unit_model:
        """Возвращает базовую единицу, в которой сохранено количество."""
        return self.__unit

    @property
    def quantity(self) -> float:
        """Возвращает положительный приход или отрицательный расход."""
        return self.__quantity

    def validate_state(self) -> None:
        """Защищает единицу уже записанных остатков при обновлении справочников."""
        if self.unit.base_unit is not self.unit or self.item.unit.base_unit is not self.unit:
            raise arguments_exception("unit", "Базовая единица складского движения изменилась")
